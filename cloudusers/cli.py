#!/usr/bin/python

import os
import sys
import argparse
import yaml

import app
from bottle import run, debug

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--host', '-H', default='localhost')
    p.add_argument('--port', '-p', default='8080')
    p.add_argument('--reload', '-r', action='store_true')
    p.add_argument('--debug', '-d', action='store_true')
    p.add_argument('--config', '-f', default='cloudusers.yaml')
    return p.parse_args()

def main():
    opts = parse_args()
    if opts.debug:
        bottle.debug(True)

    if opts.config:
        cfdict = yaml.load(open(opts.config, 'r'))
        bottle.default_app().config.update(cfdict)

    run(host=opts.host, port=int(opts.port), reloader=opts.reload)

if __name__ == '__main__':
    main()


