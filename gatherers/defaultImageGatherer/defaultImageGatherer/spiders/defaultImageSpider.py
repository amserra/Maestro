import scrapy
# to run inside the folder from defaultImageGatherer.items import ImageItem
from scrapy.http.response import Response
from gatherers.defaultImageGatherer.defaultImageGatherer.items import ImageItem


class DefaultImageSpider(scrapy.Spider):
    name = 'defaultImageSpider'

    def start_requests(self):
        urls = getattr(self, 'urls', None)
        if urls is None:
            return

        for url in urls:
            if ('.png' in url) or ('.jpg' in url) or ('.jpeg' in url) or ('.gif' in url):
                yield scrapy.Request(url=url, callback=self.parse_image)
            else:
                yield scrapy.Request(url=url, callback=self.parse_html)

    def parse_image(self, response: Response):
        item = ImageItem()
        item['image_urls'] = [response.url]
        return item

    def parse_html(self, response: Response):
        self.log(f"Parsing {response.url}")
        item = ImageItem()
        img_urls = response.xpath('//img/@src').extract()
        item['image_urls'] = [response.urljoin(url.strip()) for url in img_urls]
        yield item

        next_url = response.xpath('//a/@href').extract_first()
        if next_url is not None:
            # for url in next_urls:
            if ('.png' in next_url) or ('.jpg' in next_url) or ('.jpeg' in next_url) or ('.gif' in next_url):
                yield response.follow(next_url, self.parse_image)
            else:
                yield response.follow(next_url, self.parse_html)
