"""
vnexpress crawler.
"""
import requests
import scrapy
import re
from datetime import datetime, timedelta

category_list = [
    "https://vnexpress.net/thoi-su",
    "https://vnexpress.net/kinh-doanh",
    "https://vnexpress.net/bat-dong-san",
    "https://vnexpress.net/khoa-hoc",
    "https://vnexpress.net/giai-tri",
    "https://vnexpress.net/the-thao",
    "https://vnexpress.net/phap-luat",
    "https://vnexpress.net/giao-duc",
    "https://vnexpress.net/suc-khoe",
    "https://vnexpress.net/doi-song",
    "https://vnexpress.net/du-lich",
    "https://vnexpress.net/so-hoa",
    "https://vnexpress.net/oto-xe-may",
    "https://vnexpress.net/the-gioi",
]

cut_off_timestamp = int((datetime.now() - timedelta(days=7)).timestamp())
COMMENT_LIMIT_PER_QUERY = 200


def get_article_id(url):
    try:
        match = re.search(r'-(\d+).html', url)
        return int(match.group(1)) if match else 0
    except (AttributeError, TypeError, ValueError):
        return 0


def get_article_details(article_id_list):
    resp = requests.get("https://gw.vnexpress.net/ar/get_basic",
                        params={
                            "data_select": "title,lead,share_url,article_type,original_cate,site_id,publish_time",
                            "article_id": ','.join([str(article_id) for article_id in article_id_list if article_id != 0])
                        }
                        )
    resp.raise_for_status()
    return resp.json()["data"]


def generate_next_page_url(current_url):
    if '-p' in current_url:
        current_page_number = int(current_url.split('-p')[-1])
        next_page_url = f"{current_url.rsplit('-p', 1)[0]}-p{current_page_number + 1}"
    else:
        next_page_url = f"{current_url.rstrip('/')}-p2"
    return next_page_url


def get_comment_userlike(article, offset=0):
    num_like = 0
    resp = requests.get("https://usi-saas.vnexpress.net/index/get",
                        params={
                            "offset": offset,
                            "limit": COMMENT_LIMIT_PER_QUERY,
                            "sort": "like",
                            "tab_active": "most_like",
                            "siteid": article["site_id"],
                            "objectid": article["article_id"],
                            "objecttype": article["article_type"],
                            "categoryid": article["original_cate"]
                        }
                        )
    resp.raise_for_status()
    data = resp.json()

    if len(data["data"]["items"]) > 0:
        num_like += sum(comment["userlike"] for comment in data["data"]["items"])

        last_comment = data["data"]["items"][-1]
        if last_comment["userlike"] > 0:
            # If the last comment has userlike > 0, recursively call the function with an increased offset
            num_like += get_comment_userlike(article, offset + COMMENT_LIMIT_PER_QUERY)

    return num_like


class VnexpressSpider(scrapy.Spider):
    name = 'vnexpress'
    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': 'data/vnexpress.json',
        'FEED_EXPORT_ENCODING': 'utf-8',
        'FEED_EXPORT_INDENT': 4,
    }

    start_urls = category_list

    def parse(self, response):
        page_url = response._url

        article_id_list = [get_article_id(a.xpath('div/a/@href').get()) for a in response.xpath('//article')]
        article_list = get_article_details(article_id_list)
        for article in article_list:
            if article.get("publish_time") > cut_off_timestamp:
                article["page_url"] = page_url
                article["userlike"] = get_comment_userlike(article)
                yield article

        if article_list[-1].get("publish_time") > cut_off_timestamp:
            yield scrapy.Request(url=generate_next_page_url(page_url), callback=self.parse)
