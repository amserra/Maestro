import importlib.util
import os
import shutil
from context.models import SearchContext, Fetcher, Configuration, AdvancedConfiguration, APIResults, ImageData, PostProcessor, Filter, THUMB_SIZE
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


@app.task(bind=True)
def run_default_gatherer(self, urls, context_id):
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
    crawler_settings = {
        'SPIDER_MODULES': 'gatherers.defaultImageGatherer.defaultImageGatherer.spiders',
        'ITEM_PIPELINES': {
            # 'scrapy.pipelines.images.ImagesPipeline': 1
            'gatherers.defaultImageGatherer.defaultImageGatherer.pipelines.CustomImagesPipeline': 300
        },
        'IMAGES_STORE': context_data_path,
        'IMAGES_MIN_HEIGHT': 110,
        'IMAGES_MIN_WIDTH': 110,
        'IMAGES_THUMBS': {
            'big': THUMB_SIZE,
        },
        'LOG_FILE': log_file,
        'TELNETCONSOLE_ENABLED': False
    }

    process = CrawlerProcess(crawler_settings)
    process.crawl('defaultImageSpider', urls=urls)
    process.start()

    if context.configuration.data_type == Configuration.IMAGES:
        # Copy thumbnails to the media folder and add entries to DB
        thumbs_folder = os.path.join(context_data_path, 'thumbs')
        original_folder = os.path.join(context_data_path, 'full')
        thumbs_media_folder = os.path.join(settings.MEDIA_ROOT, context.owner_code, context.code)

        if os.path.isdir(thumbs_folder):
            os.makedirs(thumbs_media_folder, exist_ok=True)
            files = os.listdir(thumbs_folder)

            objs = []
            for file in files:
                file_path_in_thumb_media_folder = os.path.join(thumbs_folder, file)
                shutil.copy2(file_path_in_thumb_media_folder, thumbs_media_folder)
                # Add entries to DB
                obj = ImageData.objects.filter(context=context, data=os.path.join(original_folder, file))
                if not obj.exists():
                    objs.append(ImageData(
                        context=context,
                        data=os.path.join(original_folder, file),
                        data_thumb=os.path.join(thumbs_folder, file),
                        data_thumb_media=file_path_in_thumb_media_folder
                    ))
            ImageData.objects.bulk_create(objs)

    context.status = SearchContext.FINISHED_GATHERING_DATA
    context.save()

    if context.configuration.advanced_configuration and context.configuration.advanced_configuration.yield_after_gathering_data:
        context.status = SearchContext.WAITING_DATA_REVISION
        context.save()
    else:
        # TODO: CONTINUE PROCESS
        pass

    return True


@app.task(bind=True)
def run_post_processors(self, context_id):
    context = SearchContext.objects.get(id=context_id)
    datastream = context.datastream
    # post processors only used if context has advanced configuration
    advanced_configuration = context.configuration.advanced_configuration
    if not datastream.exists():
        return False

    context.status = SearchContext.POST_PROCESSING
    context.save()

    post_processors = advanced_configuration.post_processors.filter(is_active=True)

    for post_processor in post_processors:
        if post_processor.type == PostProcessor.PYTHON_SCRIPT:
            spec = importlib.util.spec_from_file_location(post_processor.name, post_processor.path)
            post_processor_script = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(post_processor_script)

            # Post processors shouldn't return exceptions, but for safety it's better to catch if one occurs
            try:
                for data in datastream:
                    result = post_processor_script.main(data.data)
                    if result is not None:
                        if post_processor.kind == PostProcessor.DATA_MANIPULATION:
                            if post_processor.data_type == Configuration.IMAGES:
                                # TODO: Not needed yet! Use functions in utils/image. What is the input? PIL object?
                                pass
                            else:
                                data.data = result
                        elif post_processor.kind == PostProcessor.METADATA_RETRIEVAL:
                            data.metadata = result
                        data.save()

            except Exception as ex:
                print(f"Post-processor {post_processor} failed:\n{ex}")

    context.status = SearchContext.FINISHED_POST_PROCESSING
    context.save()

    return True


def get_used_builtin_filters(config: AdvancedConfiguration):
    """Given an advanced configuration, returns the list of builtin filters used"""
    filter_list = set()
    if config.start_date is not None or config.end_date is not None:
        filter_list.add(Filter.objects.get(name='Date filter'))
    if config.location is not None and config.radius is not None:
        filter_list.add(Filter.objects.get(name='Geolocation filter'))
    # Add other builtin filters here
    return filter_list


@app.task(bind=True)
def run_filters(self, post_processors_result, context_id):
    if not post_processors_result:  # something went wrong on the post-processors stage
        return False

    context = SearchContext.objects.get(id=context_id)
    datastream = context.datastream
    advanced_configuration = context.configuration.advanced_configuration

    if not datastream.exists():
        return False

    context.status = SearchContext.FILTERING
    context.save()

    custom_selected_filters = set(advanced_configuration.filters.filter(is_active=True, is_builtin=False))
    builtin_filters = get_used_builtin_filters(advanced_configuration)
    filters = custom_selected_filters.union(builtin_filters)
    filterable_data = advanced_configuration.get_filterable_data()

    for _filter in filters:
        if _filter.type == PostProcessor.PYTHON_SCRIPT:
            spec = importlib.util.spec_from_file_location(_filter.name, _filter.path)
            filter_script = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(filter_script)

            # Post processors shouldn't return exceptions, but for safety it's better to catch if one occurs
            try:
                for data in datastream:
                    result = filter_script.main(data.data, data.metadata, filterable_data)
                    if (result is None and advanced_configuration.strict_filtering is True) or (result is False):
                        # Mark the data object as filtered
                        data.filtered = True
                        data.save()
                    else:
                        data.filtered = False
                        data.save()

            except Exception as ex:
                print(f"Filter {_filter} failed:\n{ex}")

    context.status = SearchContext.FINISHED_FILTERING
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
def delete_context_folder(self, context_id):
    context = SearchContext.objects.get(id=context_id)
    context_folder = context.context_folder
    context_folder_media = context.context_folder_media

    # Delete from DB
    if context.configuration:
        if context.configuration.advanced_configuration:
            context.configuration.advanced_configuration.delete()
        context.configuration.delete()
    context.delete()

    try:
        shutil.rmtree(context_folder)
        shutil.rmtree(context_folder_media)
        return True
    except Exception as e:
        print(e)
        return False
