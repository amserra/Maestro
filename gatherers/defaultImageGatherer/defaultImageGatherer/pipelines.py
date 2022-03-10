# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import hashlib
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.python import to_bytes


class DefaultimagegathererPipeline:
    def process_item(self, item, spider):
        return item


class CustomImagesPipeline(ImagesPipeline):

    def thumb_path(self, request, thumb_id, response=None, info=None):
        thumb_guid = hashlib.sha1(to_bytes(request.url)).hexdigest()
        return f'thumbs/{thumb_guid}.jpg'
