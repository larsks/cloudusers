#!/usr/bin/python

import os
import sys
import argparse

from bottle import route, static_file

@route('/static/<filename>')
def static(path):
    '''Serve up static files from the `static/` directory.'''
    return static_file(filename, 
            root=os.path.join(os.path.dirname(__file__), '..', 'static'))

