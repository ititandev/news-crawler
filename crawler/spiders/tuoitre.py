import requests
import scrapy
import re
from datetime import datetime, timedelta

class TuoitreSpider(scrapy.Spider):
    name = 'tuoitre'
    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': 'data/tuoitre.json',
        'FEED_EXPORT_ENCODING': 'utf-8',
        'FEED_EXPORT_INDENT': 4,
    }

    category_list = [
        "https://tuoitre.vn/timeline/3/trang-1.htm",  # Thoi su
        "https://tuoitre.vn/timeline/2/trang-1.htm",  # The gioi
        "https://tuoitre.vn/timeline/6/trang-1.htm",  # Phap luat
    ]

    COMMENT_LIMIT_PER_QUERY = 200
    cut_off_timestamp = int((datetime.now() - timedelta(days=7)).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).timestamp())

    def start_requests(self):
        for url in self.category_list:
            yield scrapy.Request(url, self.parse)

    def parse(self, response):
        page_url = response._url
        article_list = response.xpath('//a[@class="box-category-link-title"]')

        for i, a in enumerate(article_list):
            article = self.extract_article_data(a, page_url)

            if self.get_publish_time(article) >= self.cut_off_timestamp:
                if i == len(article_list) - 1:
                    yield scrapy.Request(url=self.generate_next_page_url(page_url), callback=self.parse)
                yield article

    def extract_article_data(self, article_selector, page_url):
        article = {'page_url': page_url}
        attributes = ["data-type", "href", "title", "data-linktype", "data-id"]

        for attr in attributes:
            article[attr] = article_selector.xpath(f'@{attr}').get()

        return article

    def get_publish_time(self, article):
        return int(datetime.strptime(article["data-id"][:8], "%Y%m%d").timestamp())

    def generate_next_page_url(self, current_url):
        match = re.search(r'(.*?/trang-)(\d+)\.htm', current_url)

        if match:
            base_url, page_number = match.group(1), int(match.group(2))
            return f"{base_url}{page_number + 1}.htm"
        else:
            print("Unable to extract base URL and page number from the URL.")
            return None
