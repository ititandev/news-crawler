#!/bin/bash
cd /opt/news-crawler

if ! pgrep -f "scrapy crawl vnexpress" > /dev/null; then
    timeout 20m scrapy crawl vnexpress -L ERROR &
else
    echo "Similar process is already running. Exiting..."
fi


if ! pgrep -f "scrapy crawl tuoitre" > /dev/null; then
    timeout 20m scrapy crawl tuoitre -L ERROR &
else
    echo "Similar process is already running. Exiting..."
fi

wait -n
