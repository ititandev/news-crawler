# News-crawler

This project contains the code for scraping vnexpress.net, tuoitre.vn and lists out the top 10 articles from last week, ranked by the total number of likes in “Ý kiến" section of the article

# Usage

- Make sure python3 is installed
- Download the source code into `/opt/news-crawler`
- Install necessary packages
```
pip install -r requirements.txt
```
- Run the web server with the following command
```bash
python app.py
```

- Install cronjob with `crontab -e`
```
*/30 * * * * bash /opt/news-crawler/crontab.sh
```
- Optional: Run crawler manually with the following commands:
```bash
scrapy crawl vnexpress
scrapy crawl tuoitre
```
# How it works?

## About scrapy
`Scrapy` is a fast high-level web crawling and web scraping framework, used to crawl websites and extract structured data from their pages. It can be used for a wide range of purposes, from data mining to monitoring and automated testing.

Built-in middleware and pipelines and asynchronous processing make `scrapy` is appropriate for this kind of task.

## VNExpress Crawler
The crawler starts with predefined category links and extracts article_id from `<article>` tag.

After that, the following API is used to get more details about that article, such as `title`, `original_cate`, `site_id`, `article_type` and `publish_time`:
```
https://gw.vnexpress.net/ar/get_basic?data_select=title,lead,share_url,article_type,original_cate,site_id,publish_time&article_id=<comma-separated-list>
```

It also continues with the next page if publish_time of the last article is still in a 7-day time window.

Then another API is used to get the comment list and count number of likes across pages
```
https://usi-saas.vnexpress.net/index/get?offset=0&limit=200&sort=like&objecttype=<article_type>&siteid=<site_id>&categoryid=<original_cate>&tab_active=most_like&objectid=<article_id>
```

Finally, `heapq.nlargest` is used to get top 10 of articles by number of likes by using a heap structure and export it to `vnexpress-top10.json`
## Tuoitre Crawler
The crawler starts with predefined category links and extracts article_id from `<a class="box-category-link-title">` tag. First 8 characters of the article_id is also considered as `publish_time` and compared with a 7-day time window to decide whether the next page is necessary to crawl

Then an API is used to get the comment list and count nubmer of likes across pages
```
https://id.tuoitre.vn/api/getlist-comment.api?pageindex=1&pagesize=50&objId=<article_id>&objType=1&sort=2
```

Finally, `heapq.nlargest` is used to get top 10 of articles by number of likes by using a heap structure and export it to `tuoitre-top10.json`
## Webserver
The web server essentially reads the latest data from `<crawler>-top10.json` or `<crawler>-top10.bak.json` and renders a simple UI for users.

There are 3 main HTTP endpoints:
- `/` to serve index.html
- `/run_vnexpress` to trigger vnexpress crawler if it's not running yet
- `/run_tuoitre` to trigger tuoitre crawler if it's not running yet

The cronjob also triggers the above jobs every 30 minutes, with a timeout of 20 minutes for each job.