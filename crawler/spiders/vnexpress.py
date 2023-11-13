"""
vnexpress crawler.
"""
import json
import os
import shutil

import requests
import scrapy
import re
from datetime import datetime, timedelta
import heapq

class VnexpressSpider(scrapy.Spider):
    name = 'vnexpress'
    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': 'data/vnexpress.json',
        'FEED_EXPORT_ENCODING': 'utf-8',
        'FEED_EXPORT_INDENT': 4,
    }

    def __init__(self, *args, **kwargs):
        super(VnexpressSpider, self).__init__(*args, **kwargs)
        self.start_urls = [
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
        self.cut_off_timestamp = int((datetime.now() - timedelta(days=7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).timestamp())
        self.comment_limit = 200
        self.article_list = []

        if os.path.exists('%s-top10.json' % self.name):
            shutil.move('%s-top10.json' % self.name, '%s-top10.bak.json' % self.name)
        if os.path.exists('data/vnexpress.json'):
            os.remove('data/vnexpress.json')


    def parse(self, response):
        page_url = response._url

        article_id_list = [self.get_article_id(a.xpath('div/a/@href').get()) for a in response.xpath('//article')]
        article_list = self.get_article_details(article_id_list)
        for article in article_list:
            if article.get("publish_time") > self.cut_off_timestamp:
                article["page_url"] = page_url
                article["like"] = self.get_comment_like(article)
                self.article_list.append(article)
                yield article

        if len(article_list) > 0 and article_list[-1].get("publish_time") > self.cut_off_timestamp:
            yield scrapy.Request(url=self.generate_next_page_url(page_url), callback=self.parse)

    def close(self, reason):
        top10 = heapq.nlargest(10, self.article_list, key=lambda x: x['like'])
        stats = self.crawler.stats.get_stats()
        with open('%s-top10.json' % self.name, 'w', encoding='utf-8') as f:
            json.dump({"finish_reason": stats["finish_reason"],
                       "finish_time": str(stats["finish_time"]),
                       "elapsed_time_seconds": stats["elapsed_time_seconds"],
                       "data": top10
                       }, f, ensure_ascii=False, indent=4)

    @staticmethod
    def get_article_id(url):
        try:
            match = re.search(r'-(\d+).html', url)
            return int(match.group(1)) if match else 0
        except (AttributeError, TypeError, ValueError):
            return 0

    def get_article_details(self, article_id_list):
        resp = requests.get("https://gw.vnexpress.net/ar/get_basic",
                            params={
                                "data_select": "title,lead,share_url,article_type,original_cate,site_id,publish_time",
                                "article_id": ','.join([str(i) for i in article_id_list if i != 0])
                            }
                            )
        resp.raise_for_status()
        return resp.json()["data"]

    def generate_next_page_url(self, current_url):
        if '-p' in current_url:
            current_page_number = int(current_url.split('-p')[-1])
            next_page_url = f"{current_url.rsplit('-p', 1)[0]}-p{current_page_number + 1}"
        else:
            next_page_url = f"{current_url.rstrip('/')}-p2"
        return next_page_url

    def get_comment_like(self, article, offset=0):
        num_like = 0
        resp = requests.get("https://usi-saas.vnexpress.net/index/get",
                            params={
                                "offset": offset,
                                "limit": self.comment_limit,
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
                num_like += self.get_comment_like(article, offset + self.comment_limit)

        return num_like

