#!/usr/bin/env python
from bottle import Bottle, run, request, response, redirect, request, abort
from subprocess import Popen, PIPE
from itertools import islice
import os
import sys
import glob
import datetime

#import bottle
#bottle.debug(True)
app = Bottle()


def ts_to_date(ts):
    d=datetime.datetime.fromtimestamp(float(ts))
    return d.strftime("%Y-%m-%d %H:%M:%S.%f")

def fix_ts(line):
    ts, rest = line.split("\t", 1)
    return ts_to_date(ts) + "\t" + rest

def collect_filenames(log_type):
    log_dir = app.config['log_dir']
    pattern = os.path.join(log_dir, "*", "%s.*" % log_type)
    files = sorted(glob.glob(pattern))
    return files 



def do_search(filename, q, context_q=None):
    if filename.endswith("lzo"):
        f = Popen(["lzop", "-dc", filename], stdout=PIPE).stdout
    elif filename.endswith("gz"):
        f = Popen(["gzip", "-dc", filename], stdout=PIPE).stdout
    else:
        f = open(filename)

    out = Popen(["grep", q], stdin=f, stdout=PIPE).stdout
    if context_q:
        out = Popen(["grep", "-C", "20", context_q], stdin=out, stdout=PIPE).stdout

    try:
        for line in out:
            yield fix_ts(line)
    finally:
        f.close()

def search_all(log_type, files, q):
    log_files = collect_filenames(log_type)
    files_to_search = log_files[-files:]
    for f in files_to_search:
        for r in do_search(f, q):
            yield r

def search_file(log_type, filename, q):
    log_files = collect_filenames(log_type)
    files_to_search = [f for f in log_files if filename in f]
    for f in files_to_search:
        for r in do_search(f, q):
            yield r

@app.route("/list/:log")
def list(log):
    log_files = collect_filenames(log)
    return {"files": log_files}

@app.route("/search/:log")
def search(log):
    q  = request.GET.get("q",   "").strip()
    filename = request.GET.get("filename",  "").strip()
    files = int(request.GET.get("files",  "2").strip())

    if "." in log:
        abort(500, "invalid parameter 'log'")

    response.content_type = "text/plain"
    if filename:
        return search_file(log, filename, q)
    else:
        return search_all(log, files, q)

def main():
    log_dir = sys.argv[1]
    app.config['log_dir'] = log_dir
    run(app, host='0.0.0.0', port=8000)

if __name__ == "__main__":
    main()
