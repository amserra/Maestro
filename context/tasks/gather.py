import os
import shutil
from context.models import SearchContext, THUMB_SIZE, Configuration, ImageData
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from django.conf import settings
from maestro.celery import app


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
