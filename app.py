import json
import subprocess

import psutil as psutil
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


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
            if 'crawl %s' % spider in ' '.join(process.cmdline()):
                return True
    except:
        pass
    return False


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


@app.route('/run_vnexpress')
def run_vnexpress():
    if not is_crawl_running("vnexpress"):
        subprocess.Popen(['timeout', '20m', 'scrapy', 'crawl', 'vnexpress', '-L', 'ERROR'])
    return redirect(url_for('index'))


@app.route('/run_tuoitre')
def run_tuoitre():
    if not is_crawl_running("tuoitre"):
        subprocess.Popen(['timeout', '20m', 'scrapy', 'crawl', 'tuoitre', '-L', 'ERROR'])
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)
