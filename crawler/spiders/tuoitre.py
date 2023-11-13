import os
import shutil

import requests
import scrapy
import re
from datetime import datetime, timedelta
import json
import heapq


class TuoitreSpider(scrapy.Spider):
    name = 'tuoitre'
    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': 'data/tuoitre.json',
        'FEED_EXPORT_ENCODING': 'utf-8',
        'FEED_EXPORT_INDENT': 4,
    }

    def __init__(self, *args, **kwargs):
        super(TuoitreSpider, self).__init__(*args, **kwargs)
        self.start_urls = [
            "https://tuoitre.vn/timeline/3/trang-1.htm",        # Thoi su
            "https://tuoitre.vn/timeline/2/trang-1.htm",        # The gioi
            "https://tuoitre.vn/timeline/6/trang-1.htm",        # Phap luat
            "https://tuoitre.vn/timeline/11/trang-1.htm",       # Kinh doanh
            "https://tuoitre.vn/timeline/200029/trang-1.htm",   # Cong nghe
            "https://tuoitre.vn/timeline/659/trang-1.htm",      # Xe
            "https://tuoitre.vn/timeline/100/trang-1.htm",      # Du lich
            "https://tuoitre.vn/timeline/7/trang-1.htm",        # Nhip song tre
            "https://tuoitre.vn/timeline/200017/trang-1.htm",   # Van hoa
            "https://tuoitre.vn/timeline/10/trang-1.htm",       # Giai tri
            "https://tuoitre.vn/timeline/1209/trang-1.htm",     # The thao
            "https://tuoitre.vn/timeline/13/trang-1.htm",       # Giao duc
            "https://tuoitre.vn/timeline/204/trang-1.htm",      # Nha dat
            "https://tuoitre.vn/timeline/12/trang-1.htm",       # Suc khoe
        ]
        self.cut_off_timestamp = int((datetime.now() - timedelta(days=7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).timestamp())
        self.comment_limit = 50
        self.article_list = []
        self.article_set = set()

        if os.path.exists('%s-top10.json' % self.name):
            shutil.move('%s-top10.json' % self.name, '%s-top10.bak.json' % self.name)
        if os.path.exists('data/%s.json' % self.name):
            os.remove('data/%s.json' % self.name)

    def parse(self, response):
        page_url = response._url
        article_selector = response.xpath('//a[@class="box-category-link-title"]')
        articles = self.extract_articles(article_selector, page_url)

        if len(articles) > 0 and articles[-1]["publish_time"] >= self.cut_off_timestamp:
            yield scrapy.Request(url=self.generate_next_page_url(page_url), callback=self.parse)

        for article in articles:
            if article["data-id"] not in self.article_set:
                self.article_set.add(article["data-id"])
                self.article_list.append(article)
                yield article

    def close(self, reason):
        top10 = heapq.nlargest(10, self.article_list, key=lambda x: x['like'])
        stats = self.crawler.stats.get_stats()
        with open('%s-top10.json' % self.name, 'w', encoding='utf-8') as f:
            json.dump({"finish_reason": stats["finish_reason"],
                       "finish_time": str(stats["finish_time"]),
                       "elapsed_time_seconds": stats["elapsed_time_seconds"],
                       "data": top10
                       }, f, ensure_ascii=False, indent=4)

    def extract_articles(self, article_selector, page_url):
        article_list = []
        for selector in article_selector:
            article = {'page_url': page_url}
            attributes = ["data-type", "href", "title", "data-linktype", "data-id"]
            for attr in attributes:
                article[attr] = selector.xpath(f'@{attr}').get()

            article["publish_time"] = int(datetime.strptime(article["data-id"][:8], "%Y%m%d").timestamp())
            if article["publish_time"] >= self.cut_off_timestamp > 0:
                like = self.get_comment_like(article["data-id"])
                if like > 0:
                    article["like"] = like
                    article_list.append(article)

        return article_list

    def generate_next_page_url(self, current_url):
        match = re.search(r'(.*?/trang-)(\d+)\.htm', current_url)

        if match:
            base_url, page_number = match.group(1), int(match.group(2))
            return f"{base_url}{page_number + 1}.htm"
        else:
            print("Unable to extract base URL and page number from the URL.")
            return None

    def get_comment_count(self, article_id_list):
        url = "https://id.tuoitre.vn/api/getcount-comment.api"

        headers = {'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        response = requests.request("POST", url, headers=headers, data={"ids": ','.join(article_id_list)})
        response.raise_for_status()

        return [i.get("object_id") for i in response.json().get("Data")]

    def get_comment_like(self, article_id, index=1):
        num_like = 0
        resp = requests.get("https://id.tuoitre.vn/api/getlist-comment.api", params={
            "sort": 2,
            "objType": 1,
            "objId": article_id,
            "pagesize": self.comment_limit,
            "pageindex": index
        })
        resp.raise_for_status()
        try:
            comments = json.loads(resp.json()["Data"])
            if len(comments) > 0:
                num_like += sum(comment.get("likes") for comment in comments)
                if comments[-1].get("likes") > 0:
                    # If the last comment has like > 0, recursively call the function with an increased index
                    num_like += self.get_comment_like(article_id, index + 1)
            return num_like
        except:
            return num_like
