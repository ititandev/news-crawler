import os
import json
import subprocess

import psutil as psutil
from flask import Flask, render_template, request, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
sched = BackgroundScheduler(daemon=True)
timeout = int(os.environ.get("TIMEOUT", "60"))


def load_data(file):
    try:
        with open("%s.json" % file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(e)
        try:
            with open("%s.bak.json" % file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []


def is_crawl_running(spider):
    try:
        for process in psutil.process_iter(['pid', 'name', 'cmdline']):
            if '%s' % spider in ' '.join(process.cmdline()):
                return True
    except:
        pass
    return False


def get_crawler_command(crawler):
    return ['timeout', '%dm' % timeout, 'scrapy', 'crawl', crawler, '-L', 'WARNING', ';']


@app.route('/run_vnexpress')
def run_vnexpress():
    if not is_crawl_running("vnexpress"):
        subprocess.Popen(get_crawler_command("vnexpress"))
    return redirect(url_for('index'))


@app.route('/run_tuoitre')
def run_tuoitre():
    if not is_crawl_running("tuoitre"):
        subprocess.Popen(get_crawler_command("tuoitre"))
    return redirect(url_for('index'))


def run_crawlers():
    if not is_crawl_running("tuoitre"):
        subprocess.run(get_crawler_command('tuoitre'), stdout=subprocess.PIPE, text=True)
    if not is_crawl_running("vnexpress"):
        subprocess.run(get_crawler_command('vnexpress'), stdout=subprocess.PIPE, text=True)


@app.route('/')
def index():
    vnexpress = load_data("vnexpress-top10")
    tuoitre = load_data("tuoitre-top10")

    return render_template('index.html',
                           vnexpress=vnexpress,
                           tuoitre=tuoitre,
                           vnexpress_running=is_crawl_running("vnexpress"),
                           tuoitre_running=is_crawl_running("tuoitre"),
                           interval=timeout*2
                           )


sched.add_job(run_crawlers, 'interval', minutes=timeout*2)
sched.start()

if __name__ == '__main__':
    # HOST=unix://app.sock to listen unix socket instead
    app.run(host=os.environ.get('HOST', "0.0.0.0"), port=os.environ.get('PORT', 8080), debug=True)
