import json
import subprocess

import psutil as psutil
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


def load_data(file):
    result = []
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
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'scrapy crawl %s' % spider in process.info['cmdline']:
            return True
    return False


@app.route('/')
def index():
    vnexpress = load_data("vnexpress-top10")
    print(vnexpress)
    tuoitre = load_data("tuoitre-top10")

    return render_template('index.html', vnexpress=vnexpress, tuoitre=tuoitre)


@app.route('/run_vnexpress')
def run_vnexpress():
    subprocess.Popen(['scrapy', 'crawl', 'vnexpress'])
    return redirect(url_for('index'))

@app.route('/run_tuoitre')
def run_tuoitre():
    subprocess.Popen(['scrapy', 'crawl', 'tuoitre'])
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)
