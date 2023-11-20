import os
import json
import subprocess

import psutil as psutil
from flask import Flask, render_template, request, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
sched = BackgroundScheduler(daemon=True)


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


@app.route('/run_vnexpress')
def run_vnexpress():
    if not is_crawl_running("vnexpress"):
        subprocess.Popen(['timeout', '60m', 'scrapy', 'crawl', 'vnexpress', '-L', 'WARNING'])
    return redirect(url_for('index'))


@app.route('/run_tuoitre')
def run_tuoitre():
    if not is_crawl_running("tuoitre"):
        subprocess.Popen(['timeout', '60m', 'scrapy', 'crawl', 'tuoitre', '-L', 'WARNING'])
    return redirect(url_for('index'))


@app.route('/')
def index():
    vnexpress = load_data("vnexpress-top10")
    tuoitre = load_data("tuoitre-top10")

    return render_template('index.html',
                           vnexpress=vnexpress,
                           tuoitre=tuoitre,
                           vnexpress_running=is_crawl_running("vnexpress"),
                           tuoitre_running=is_crawl_running("tuoitre")
                           )


sched.add_job(run_vnexpress, 'interval', minutes=60)
sched.add_job(run_tuoitre, 'interval', minutes=60)
sched.start()

if __name__ == '__main__':
    # HOST=unix://app.sock to listen unix socket instead
    app.run(host=os.environ.get('HOST', "0.0.0.0"), port=os.environ.get('PORT', 8080), debug=True)
