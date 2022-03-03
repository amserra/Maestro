import scrapy


class DefaultUrlGatherSpider(scrapy.Spider):
    name = 'defaultUrlGather'

    def start_requests(self):
        url = 'https://google.com/'
        query = getattr(self, 'query', None)
        if query is not None:
            query = query.replace(' ', '+')
            url = url + 'search?q=' + query
        self.log(f"URL is {url}")
        yield scrapy.Request(url, self.parse)

    # def parse(self, response):
        
