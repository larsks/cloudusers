#!/usr/bin/python

import sys
import os
import bottle

sys.path.append(os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))
import cloudusers
application = bottle.default_app()

