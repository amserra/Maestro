import importlib.util
import os
import shutil
from context.models import SearchContext, Fetcher, Configuration, AdvancedConfiguration
from maestro.celery import app
from django.conf import settings


def fetcher_parameters(configuration: Configuration, advanced_configuration: AdvancedConfiguration):
    search_string = configuration.search_string
    country_code = advanced_configuration.country_of_search if advanced_configuration and advanced_configuration.country_of_search else AdvancedConfiguration.DEFAULT_COUNTRY_OF_SEARCH
    return search_string, country_code


@app.task(bind=True)
def fetch_urls(self, context_id):
    list_of_urls = []

    context = SearchContext.objects.get(id=context_id)
    configuration = context.configuration
    advanced_configuration = context.configuration.advanced_configuration

    if advanced_configuration:
        fetchers = list(advanced_configuration.fetchers.all())
    else:
        fetchers = list(Fetcher.objects.filter(is_active=True, is_default=True))

    for fetcher in fetchers:
        if fetcher.type == Fetcher.PYTHON_SCRIPT:
            spec = importlib.util.spec_from_file_location(fetcher.name, fetcher.path)
            fetcher_script = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fetcher_script)

            fetcher_params = fetcher_parameters(configuration, advanced_configuration)
            try:
                result = fetcher_script.main(*fetcher_params)
                list_of_urls.extend(result)
            except Exception as ex:
                print(f"Fetcher {fetcher} failed:\n{ex}")

    if advanced_configuration and advanced_configuration.seed_urls != []:
        list_of_urls.extend(advanced_configuration.seed_urls)

    # Write in file
    with open(f'{settings.CONTEXTS_DATA_DIR}/{context.owner_code}/{context.code}/urls.txt', 'w') as f:
        f.write(str(list_of_urls))

    return list_of_urls


@app.task(bind=True)
def copy_default_gatherers(self, gatherers_list):
    pass


@app.task(bind=True)
def create_context_folder(self, owner_code, context_code):
    # Creates the folder and the intermediary folders if they not exist
    # If these folders already exist, keep everything and continue
    base_context_dir = f'{settings.BASE_DIR}/contexts_data/{owner_code}/{context_code}'
    os.makedirs(base_context_dir, exist_ok=True)
    os.makedirs(f'{base_context_dir}/gatherers', exist_ok=True)
    os.makedirs(f'{base_context_dir}/data', exist_ok=True)
    return True


@app.task(bind=True)
def delete_context_folder(self, owner_code, context_code):
    try:
        shutil.rmtree(f'{settings.BASE_DIR}/contexts_data/{owner_code}/{context_code}')
        return True
    except Exception as e:
        print(e)
        return False
