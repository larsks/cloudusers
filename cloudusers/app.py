#!/usr/bin/python

import os
import sys
import string
import random

import bottle
from bottle import route,post,request,response,static_file
from bottle import jinja2_template as template

import novaclient.v1_1.client as nova
import novaclient.exceptions
import keystoneclient.v2_0.client as keystone
import keystoneclient.exceptions

import markdown

def filter_markdown(s):
    '''Allows us to embed Markdown markup inside
    {% filter markdown %} blocks.'''
    return markdown.markdown(s)

def render(view, **kwargs):
    '''This wraps template rendering so that we can provide
    a standard set of variables into the templates.'''
    return template(view,
            environ=request.environ,
            template_settings={ 'filters':
                { 'markdown': filter_markdown }},
            **kwargs)

@route('/style.css')
def style_css():
    '''Serves up our stylesheet.  This can't be a static file because we
    need to do template subsitution on URL paths.'''
    response.set_header('Content-type', 'text/css')
    return render('style.css')

@route('/static/<path:path>')
def static(path):
    '''Serve up static files from the `static/` directory.'''
    return static_file(path, 
            root=os.path.join(os.path.dirname(__file__), '..', 'static'))

@route('/auth/debug')
def debug():
    '''Dump various internal data to a web page.'''
    if request.app.config.get('debug'):
        return render('debug.html',
                config = request.app.config,
                )
    else:
        return render('error.html',
                error='Debug mode is disabled.',
                )

@route('/')
def index(message=None):
    return render('index.html', 
            message=message,
            )

def authenticated(fn):
    '''A function decorator for functions that require an authenticated
    user.  Ensures that `REMOTE_USER` (and other criticals variables) are
    available in the environment and sets up a keystone client.'''

    def _(*args, **kwargs):
        service_endpoint = request.app.config.get('service_endpoint',
                request.environ.get('SERVICE_ENDPOINT'))
        service_token = request.app.config.get('service_token',
                request.environ.get('SERVICE_TOKEN'))

        if 'REMOTE_USER' not in request.environ:
            return render('error.html',
                    error='Configuration error (1).')

        if not service_endpoint or not service_token:
            return render('error.html',
                    error='Configuration error (2).')

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

    return _

@route('/auth/info')
@authenticated
def info(message=None):
    uid = request.environ['REMOTE_USER']

    try:
        userrec = request.client.users.find(name=uid)
        tenantrec = request.client.tenants.get(userrec.tenantId)
        return render('userinfo.html',
                user=userrec,
                tenant=tenantrec,
                message=message,
                )
    except keystoneclient.exceptions.NotFound:
        return index(message='You do not have a SEAS cloud account.')

@route('/auth/newkey')
@authenticated
def newkey():
    '''Generate a new apikey for the authenticated user if they have
    an existing OpenStack account.'''

    uid = request.environ['REMOTE_USER']
    apikey = ''.join(random.sample(string.letters + string.digits,
            20))
    try:
        userrec = request.client.users.find(name=uid)
        tenantrec = request.client.tenants.get(userrec.tenantId)
    except keystoneclient.exceptions.NotFound:
        return index(message='You do not have a SEAS cloud account.')

    request.client.users.update_password(userrec.id, apikey)
    return render('userinfo.html',
            user=userrec,
            tenant=tenantrec,
            apikey=apikey,
            )

@route('/auth/create')
@authenticated
def create():
    '''Create a new OpenStack user, including the following:

    - Create a new tenant named "user/<username>".
    - Create a new user account.
    - Populate the "default" security group for the tenant.
    '''
    uid = request.environ['REMOTE_USER']
    apikey = ''.join(random.sample(string.letters + string.digits,
            20))

    # Does the user exist?
    try:
        userrec = request.client.users.find(name=uid)
    except keystoneclient.exceptions.NotFound:
        userrec = None

    # If the user already exists, just display account information.
    if userrec:
        return info(
                message='Found an existing SEAS Cloud account for ' \
                        'your username (%s).' % userrec.name,
                )

    # If we get this far we need to create the user.  First
    # see if the appropriate tenant already exists (which might
    # happen if someone deletes the user via the gui and leaves the tenant
    # in place).
    try:
        tenantrec = request.client.tenants.find(name='user/%s' % uid)
    except keystoneclient.exceptions.NotFound:
        tenantrec = request.client.tenants.create('user/%s' % uid)

    userrec = request.client.users.create(uid,
            apikey, '', tenant_id=tenantrec.id)

    # And now we need to create some default
    # security rules.
    if 'security rules' in request.app.config:
        # Authenticate to nova as the new user.
        nc = nova.Client(userrec.name, apikey, tenantrec.name,
                request.app.config.service_endpoint,
                service_type='compute')

        # Look up the "default" security group.
        sg = nc.security_groups.find(name='default')

        # Create security rules based on configuration.
        for rule in request.app.config['security rules']:
            try:
                sr = nc.security_group_rules.create(
                        sg.id,
                        ip_protocol=rule['protocol'],
                        from_port=rule['from port'],
                        to_port=rule['to port'])
            except novaclient.exceptions.BadRequest:
                # This probably means that the rule already exists.
                pass

    return render('userinfo.html',
            user=userrec,
            tenant=tenantrec,
            apikey=apikey,
            message='Your SEAS Cloud account is ready.',
            )

