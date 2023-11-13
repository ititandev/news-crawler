#!/bin/bash
cd /opt/news-crawler

timeout 20m scrapy crawl vnexpress -L ERROR &
timeout 20m scrapy crawl tuoitre -L ERROR &

wait -n
