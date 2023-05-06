import scrapy


class ScrapySpider(scrapy.Spider):
    name = 'scrapy'
    allowed_domains = ['asura.gg']
    start_urls = ['https://asura.gg/manga/standard-of-reincarnation/']

    def parse(self, response):
        return response.body
