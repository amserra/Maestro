import importlib.util
import os
from django.conf import settings
from datetime import datetime
from context.models import APIResults, Configuration, AdvancedConfiguration, SearchContext, Fetcher
import ast
from collections import OrderedDict
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
    search_string = configuration.search_string
    country_code = advanced_configuration.country_of_search if advanced_configuration and advanced_configuration.country_of_search else AdvancedConfiguration.DEFAULT_COUNTRY_OF_SEARCH
    return OrderedDict({
        'search_string': search_string,
        'country_code': country_code
    })


@app.task(bind=True)
def fetch_urls(self, context_id):
    list_of_urls = []

    context = SearchContext.objects.get(id=context_id)
    context.status = SearchContext.FETCHING_URLS
    context.save()

    configuration = context.configuration
    advanced_configuration = context.configuration.advanced_configuration

    if advanced_configuration:
        fetchers = list(advanced_configuration.fetchers.filter(is_active=True))
    else:
        fetchers = list(Fetcher.objects.filter(is_active=True, is_default=True))

    for fetcher in fetchers:
        if fetcher.type == Fetcher.PYTHON_SCRIPT:
            spec = importlib.util.spec_from_file_location(fetcher.name, fetcher.path)
            fetcher_script = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fetcher_script)

            fetcher_params = fetcher_parameters(configuration, advanced_configuration)
            cached_urls = cached_fetcher_urls(fetcher, fetcher_params)

            if cached_urls is not None:
                print("Using cached URLS")
                list_of_urls.extend(cached_urls)
            else:
                try:
                    result = fetcher_script.main(fetcher_params)
                    list_of_urls.extend(result)
                    save_api_result_to_cache(fetcher, fetcher_params, result)
                except Exception as ex:
                    print(f"Fetcher {fetcher} failed:\n{ex}")

    if advanced_configuration and advanced_configuration.seed_urls != []:
        list_of_urls.extend(advanced_configuration.seed_urls)

    # Save urls to context folder
    with open(f'{context.context_folder}/urls.txt', 'w') as f:
        f.write(str(list_of_urls))

    context.status = SearchContext.FINISHED_FETCHING_URLS
    context.save()
    return list_of_urls
