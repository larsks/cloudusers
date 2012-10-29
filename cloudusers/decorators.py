#!/usr/bin/python

import os
import sys
from bottle import request

import keystoneclient.v2_0.client as keystone

from apperrors import *

def filter_markdown(s):
    '''Allows us to embed Markdown markup inside
    {% filter markdown %} blocks.'''
    return markdown.markdown(s)

class render (object):
    def __init__(self, view):
        self.view = view

    def __call__(self, fn):
        def _(*args, **kwargs):
            try:
                namespace = fn(*args, **kwargs)
                return self.render(self.view, **namespace)
            except ApplicationError, detail:
                return self.render('error.html',
                        error=str(detail))

        return _

    def render(self, view, **kwargs):
                return template(self.view,
                        environ=request.environ,
                        template_settings={ 'filters':
                            { 'markdown': filter_markdown }},
                        **kwargs)

class authenticated(object):
    '''A function decorator for functions that require an authenticated
    user.  Ensures that `REMOTE_USER` (and other criticals variables) are
    available in the environment and sets up a keystone client.'''

    def __init__(self, fn):
        self.fn = fn

    def __call__(self, *args, **kwargs):
        service_endpoint = request.app.config.get('service_endpoint',
                request.environ.get('SERVICE_ENDPOINT'))
        service_token = request.app.config.get('service_token',
                request.environ.get('SERVICE_TOKEN'))

        if 'REMOTE_USER' not in request.environ:
            raise ConfigurationError()

        if not service_endpoint or not service_token:
            raise ConfigurationError()

        # If we got these from the environment, put them instead
        # our config so that they're available elsewhere in the 
        # code.
        request.app.config.service_endpoint = service_endpoint
        request.app.config.service_token = service_token

        request.client = keystone.Client(
                endpoint=service_endpoint,
                token=service_token,
                )

        return fn(*args, **kwargs)

