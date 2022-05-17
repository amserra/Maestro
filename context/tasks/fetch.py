import importlib.util
import os
from django.conf import settings
from datetime import datetime
from context.models import APIResults, Configuration, AdvancedConfiguration, SearchContext, Fetcher
import ast
from collections import OrderedDict
from context.tasks.helpers import change_status, write_log
from maestro.celery import app


def save_api_result_to_cache(fetcher, configuration, urls):
    # Write in file
    folder = os.path.join(settings.LOGS_PATH, 'apis')
    file_name = f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}_{fetcher.name.replace(" ", "_")}.json'
    full_path = os.path.join(folder, file_name)
    with open(full_path, 'w') as f:
        f.write(str(urls))
    # Save in database
    APIResults.objects.create(fetcher=fetcher, configuration=configuration, result_file=full_path)


def cached_fetcher_urls(fetcher, data):
    try:
        api_result = APIResults.objects.get(fetcher=fetcher, configuration=data)
        file = api_result.result_file
        with open(file, 'r') as f:
            list_str = f.read()
        return ast.literal_eval(list_str)
    except:
        return None


def fetcher_parameters(configuration: Configuration, advanced_configuration: AdvancedConfiguration):
    keywords = [keyword.name for keyword in configuration.keywords.all()]
    country_code = advanced_configuration.country_of_search if advanced_configuration and advanced_configuration.country_of_search else AdvancedConfiguration.DEFAULT_COUNTRY_OF_SEARCH
    return OrderedDict({
        'search_string': configuration.search_string,
        'keywords': keywords,
        'start_date': advanced_configuration.start_date if advanced_configuration and advanced_configuration.start_date else None,
        'end_date': advanced_configuration.end_date if advanced_configuration and advanced_configuration.end_date else None,
        'country_code': country_code
    })


@app.task(bind=True)
def run_fetchers(self, context_id):
    stage = 'fetch'
    list_of_urls = []

    context = SearchContext.objects.get(id=context_id)

    if context.is_stopped:
        return False

    context.number_of_iterations = context.number_of_iterations + 1
    context.save()

    change_status(SearchContext.FETCHING_URLS, context, stage, 'Started fetching URLs', True)

    configuration = context.configuration
    advanced_configuration = context.configuration.advanced_configuration

    if advanced_configuration:
        fetchers = list(advanced_configuration.fetchers.filter(is_active=True))
    else:
        fetchers = list(Fetcher.objects.filter(is_active=True, is_default=True))

    write_log(context, stage, f'Will use these fetchers: {fetchers}')

    for fetcher in fetchers:
        write_log(context, stage, f'Using fetcher \'{fetcher}\'')
        if fetcher.type == Fetcher.PYTHON_SCRIPT:
            spec = importlib.util.spec_from_file_location(fetcher.name, fetcher.path)
            fetcher_script = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fetcher_script)

            fetcher_params = fetcher_parameters(configuration, advanced_configuration)
            cached_urls = cached_fetcher_urls(fetcher, fetcher_params)

            if cached_urls is not None:
                write_log(context, stage, f'Another context has already made the same query: using {len(cached_urls)} cached URLs')
                list_of_urls.extend(cached_urls)
            else:
                try:
                    result = fetcher_script.main(fetcher_params)
                    write_log(context, stage, f'Fetched {len(result)} new URLs')
                    list_of_urls.extend(result)
                    write_log(context, stage, f'Current total number of URLs: {list_of_urls}')
                    save_api_result_to_cache(fetcher, fetcher_params, result)
                except Exception as ex:
                    print(f"Fetcher {fetcher} failed:\n{ex}")  # later, log this to a system log
                    write_log(context, stage, f'[ERROR] Fetcher \'{fetchers}\' failed. Continuing...')

    if advanced_configuration and advanced_configuration.seed_urls != []:
        list_of_urls.extend(advanced_configuration.seed_urls)
        write_log(context, stage, f'The user provided \'{len(advanced_configuration.seed_urls)}\' additional seed URLs')

    # Save urls to context folder
    with open(f'{context.context_folder}/urls.txt', 'w') as f:
        f.write(str(list_of_urls))

    write_log(context, stage, f'The final number of URLs is: {len(list_of_urls)}')
    change_status(SearchContext.FINISHED_FETCHING_URLS, context, stage, 'Finished fetching URLs. Will now gather')
    return list_of_urls
