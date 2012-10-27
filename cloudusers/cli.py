#!/usr/bin/python

import os
import sys
import argparse

import app
from bottle import run

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--host', '-H', default='localhost')
    p.add_argument('--port', '-p', default='8080')
    p.add_argument('--reload', '-r', action='store_true')
    return p.parse_args()

def main():
    opts = parse_args()
    run(host=opts.host, port=int(opts.port), reloader=opts.reload)

if __name__ == '__main__':
    main()


