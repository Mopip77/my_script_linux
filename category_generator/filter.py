#!/usr/bin/env python3
import json
import sys

def getUpdateIpynbFile():
    fp = open("/tmp/_var_www_html_ML")
    _transLog = json.loads(fp.read())
    fp.close()
    [print(f.replace(' ', '?')) for f in _transLog['update'] if f.split('.')[-1] == 'ipynb']
    # for f in filter(x.split('.')[-1] == 'ipynb' for x in _transLog['update']):
    #     print(f)

def getDelIpynbFile():
    fp = open("/tmp/_var_www_html_ML")
    _transLog = json.loads(fp.read())
    fp.close()
    [print(f.replace(' ', '?')) for f in _transLog['delete'] if f.split('.')[-1] == 'ipynb']
    # for f in filter(x.split('.')[-1] == 'ipynb' for x in _transLog['delete']):
    #     print(f)

if __name__ == "__main__":
    if sys.argv[1] == 'update':
        getUpdateIpynbFile()
    elif sys.argv[1] == 'delete':
        getDelIpynbFile()
