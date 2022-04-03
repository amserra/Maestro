import os
import shutil
from context.models import SearchContext, THUMB_SIZE, Configuration, ImageData
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from django.conf import settings

from context.tasks.helpers import change_status, write_log
from maestro.celery import app


@app.task(bind=True)
def run_default_gatherer(self, urls, context_id):
    stage = 'gather'
    context = SearchContext.objects.get(id=context_id)

    if len(urls) == 0:
        change_status(SearchContext.FAILED_GATHERING_DATA, context, stage, '[ERROR] No URLs returned from the fetching stage', True)
        return False

    change_status(SearchContext.GATHERING_DATA, context, stage, f'Started gathering data from {len(urls)} urls', True)

    # Create data store folder if not exists
    context_data_path = os.path.join(context.context_folder, 'data')
    os.makedirs(context_data_path, exist_ok=True)

    # Create log folder if not exists
    context_log_path = os.path.join(context.context_folder, 'logs')
    os.makedirs(context_log_path, exist_ok=True)

    write_log(context, stage, f'Folders to support data persistance created')

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
            write_log(context, stage, f'Downloaded {len(files)} images')
            write_log(context, stage, f'Preparing and storing images on database')

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

    change_status(SearchContext.FINISHED_GATHERING_DATA, context, stage, f'Finished gathering data')

    if context.configuration.advanced_configuration and context.configuration.advanced_configuration.yield_after_gathering_data:
        change_status(SearchContext.WAITING_DATA_REVISION, context, stage, f'The user should now review the obtained dataset')
        return False
    else:
        write_log(context, stage, 'Continuing process. Following stage is post-processing')
        return True