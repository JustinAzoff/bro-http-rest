#!/usr/bin/env python
from bottle import Bottle, run, request, response, redirect, request
from subprocess import Popen, PIPE
from itertools import islice
import os
import sys
import glob

app = Bottle()

def collect_filenames(log_type):
    log_dir = app.config['log_dir']
    pattern = os.path.join(log_dir, "*", "%s.*" % log_type)
    files = sorted(glob.glob(pattern))
    return files 

def do_search(filename, q):
    if filename.endswith("lzo"):
        f = Popen(["lzop", "-d", filename], stdout=PIPE).stdout
    else:
        f = open(filename)

    out = Popen(["grep", q], stdin=f, stdout=PIPE).stdout

    try:
        return out
    finally:
        f.close()

def search_all(log_type, files, q):
    log_files = collect_filenames(log_type)
    files_to_search = log_files[-files:]
    for f in files_to_search:
        for r in do_search(f, q):
            yield r

@app.route("/search")
def search():
    log = request.GET.get("log", "").strip()
    q  = request.GET.get("q",   "").strip()
    files = int(request.GET.get("files",  "2").strip())
    limit = int(request.GET.get("limit",  "2000").strip())

    return search_all(log, files, q)


def main():
    log_dir = sys.argv[1]
    app.config['log_dir'] = log_dir
    run(app, port=8000)

if __name__ == "__main__":
    main()
