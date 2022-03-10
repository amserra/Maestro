import importlib.util
import os
import shutil
from context.models import SearchContext, Fetcher, Configuration, AdvancedConfiguration, APIResults
from maestro.celery import app
from django.conf import settings
from scrapy.crawler import CrawlerProcess
from datetime import datetime
import ast
from collections import OrderedDict


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

    return list_of_urls


@app.task(bind=True)
def run_default_gatherer(self, urls: list[str], context_id):
    # The result of the first task (fetch_urls) will be the first argument of this task (they form a chain)
    context = SearchContext.objects.get(id=context_id)
    context.status = SearchContext.GATHERING_DATA
    context.save()

    # Create data store folder if not exists
    context_data_path = os.path.join(context.context_folder, 'data')
    os.makedirs(context_data_path, exist_ok=True)

    # Create log folder if not exists
    context_log_path = os.path.join(context.context_folder, 'logs')
    os.makedirs(context_log_path, exist_ok=True)

    log_file = os.path.join(context_log_path, f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}_gatherer.txt')
    process = CrawlerProcess({
        'SPIDER_MODULES': 'gatherers.defaultImageGatherer.defaultImageGatherer.spiders',
        'ITEM_PIPELINES': {
            # 'scrapy.pipelines.images.ImagesPipeline': 1
            'gatherers.defaultImageGatherer.defaultImageGatherer.pipelines.CustomImagesPipeline': 300
        },
        'IMAGES_STORE': context_data_path,
        'IMAGES_MIN_HEIGHT': 110,
        'IMAGES_MIN_WIDTH': 110,
        'IMAGES_THUMBS': {
            'big': (270, 270),
        },
        'LOG_FILE': log_file,
        'TELNETCONSOLE_ENABLED': False
    })
    process.crawl('defaultImageSpider', urls=urls)
    process.start()

    context.status = SearchContext.WAITING_DATA_REVISION
    context.save()

    return True


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
