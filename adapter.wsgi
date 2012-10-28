#!/usr/bin/python

import sys
import os
import site

appdir = os.path.dirname(__file__)
os.chdir(appdir)

if os.path.exists('env'):
    site.addsitedir('env/lib/python2.6/site-packages')

import bottle
import yaml

if os.path.exists('cloudusers.yaml'):
    cfdict = yaml.load(open('cloudusers.yaml', 'r'))
    bottle.default_app().config.update(cfdict)

os.chdir(appdir)
import cloudusers.app
application = bottle.default_app()

