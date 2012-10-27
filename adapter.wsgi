#!/usr/bin/python

import sys
import os
import site

appdir = os.path.dirname(__file__)
if os.path.exists(os.path.join(appdir, 'env')):
    site.addsitedir(os.path.join(appdir, 'env/lib/python2.6/site-packages'))
sys.path.append(appdir)

import bottle

os.chdir(appdir)
import cloudusers.app
application = bottle.default_app()

