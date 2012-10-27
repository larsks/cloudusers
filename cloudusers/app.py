#!/usr/bin/python

import os
import sys
import string
import random

from bottle import route,post,request,response,static_file
from bottle import jinja2_template as template

import novaclient.v1_1.client as nova
import keystoneclient.v2_0.client as keystone
from keystoneclient.exceptions import *

import markdown

def filter_markdown(s):
    return markdown.markdown(s)

def render(view, **kwargs):
    return template(view,
            environ=request.environ,
            template_settings={ 'filters':
                { 'markdown': filter_markdown }},
            **kwargs)

@route('/style.css')
def style_css():
    response.set_header('Content-type', 'text/css')
    return render('style.css')

@route('/static/<path:path>')
def static(path):
    return static_file(path, 
            root=os.path.join(os.path.dirname(__file__), '..', 'static'))

@route('/auth/debug')
def debug():
    return render('vars.html')

@route('/')
def index(message=None):
    return render('index.html', 
            message=message,
            )

def authenticated(fn):
    def _(*args, **kwargs):
        for var in ['SERVICE_ENDPOINT', 'SERVICE_TOKEN', 'REMOTE_USER']:
            if var not in request.environ:
                return render(error.html, message='Configuration error.')

        request.client = keystone.Client(
                endpoint=request.environ['SERVICE_ENDPOINT'],
                token=request.environ['SERVICE_TOKEN'],
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
    except NotFound:
        return index(message='You do not have a SEAS cloud account.')

@route('/auth/newkey')
@authenticated
def newkey():
    uid = request.environ['REMOTE_USER']
    apikey = ''.join(random.sample(string.letters + string.digits,
            20))
    try:
        userrec = request.client.users.find(name=uid)
        tenantrec = request.client.tenants.get(userrec.tenantId)
    except NotFound:
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
    uid = request.environ['REMOTE_USER']
    apikey = ''.join(random.sample(string.letters + string.digits,
            20))

    # Does the user exist?
    try:
        userrec = request.client.users.find(name=uid)
    except NotFound:
        userrec = None

    print >>sys.stderr, 'userrec:', userrec

    # if the user already exists, just update their password.
    if userrec:
        return info(
                message='Found an existing SEAS Cloud account for your username (%s).' % userrec.name,
                )

    # If we get this far we need to create the user.  First
    # see if the appropriate tenant already exists.
    try:
        tenantrec = request.client.tenants.find(name='user/%s' % uid)
    except NotFound:
        tenantrec = request.client.tenants.create('user/%s' % uid)

    userrec = request.client.users.create(uid,
            apikey, '', tenant_id=tenantrec.id)

    # And now we need to create some default
    # security rules.
    nc = nova.Client(userrec.name, apikey, tenantrec.name,
            request.environ['SERVICE_ENDPOINT'],
            service_type='compute')
    sg = nc.security_groups.find(name='default')
    sr = nc.security_group_rules.create(
            sg.id, ip_protocol='icmp',
            from_port='-1',
            to_port='-1')
    sr = nc.security_group_rules.create(
            sg.id, ip_protocol='tcp',
            from_port='22',
            to_port='22')

    return render('userinfo.html',
            user=userrec,
            tenant=tenantrec,
            apikey=apikey,
            message='Your SEAS Cloud account is ready.',
            )

