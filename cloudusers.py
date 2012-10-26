#!/usr/bin/python

import os
import sys
import argparse
import string
import random

from bottle import route,post,run,request
from bottle import jinja2_template as template

import novaclient.v1_1.client as nova
import keystoneclient.v2_0.client as keystone
from keystoneclient.exceptions import *

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--host', '-H', default='localhost')
    p.add_argument('--port', '-p', default='8080')
    return p.parse_args()

@route('/debug')
def debug():
    return template('vars.html', vars=request.environ)

@route('/')
def index(message=None):
    return template('index.html', 
            message=message,
            environ=request.environ)

@route('/auth/info')
def info(message=None):
    if 'REMOTE_USER' not in request.environ:
        return template('error.html',
                message='Not authenticated.',
                environ=request.environ)

    request.client = keystone.Client(
            endpoint=request.environ['SERVICE_ENDPOINT'],
            token=request.environ['SERVICE_TOKEN'],
            )
    uid = request.environ['REMOTE_USER']

    try:
        userrec = request.client.users.find(name=uid)
        tenantrec = request.client.tenants.get(userrec.tenantId)
        return template('userinfo.html',
                user=userrec,
                tenant=tenantrec,
                environ=request.environ,
                message=message)
    except NotFound:
        return index(message='You do not have a SEAS cloud account.')

@route('/auth/newkey')
def newkey():
    if 'REMOTE_USER' not in request.environ:
        return template('error.html',
                message='Not authenticated.',
                environ=request.environ)

    request.client = keystone.Client(
            endpoint=request.environ['SERVICE_ENDPOINT'],
            token=request.environ['SERVICE_TOKEN'],
            )
    uid = request.environ['REMOTE_USER']
    apikey = ''.join(random.sample(string.letters + string.digits,
            20))
    try:
        userrec = request.client.users.find(name=uid)
        tenantrec = request.client.tenants.get(userrec.tenantId)
    except NotFound:
        return index(message='You do not have a SEAS cloud account.')

    request.client.users.update_password(userrec.id, apikey)
    return template('userinfo.html',
            user=userrec,
            tenant=tenantrec,
            apikey=apikey,
            environ=request.environ,
            )

@route('/auth/create')
def create():
    if 'REMOTE_USER' not in request.environ:
        return template('error.html',
                message='Not authenticated.',
                environ=request.environ)

    request.client = keystone.Client(
            endpoint=request.environ['SERVICE_ENDPOINT'],
            token=request.environ['SERVICE_TOKEN'],
            )
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
                message='You already have a SEAS Cloud account.',
                )

    # If we get this far we need to create the user.  First
    # see if the appropriate tenant already exists.
    try:
        tenantrec = request.client.tenants.find(name='user/%s' % uid)
    except NotFound:
        tenantrec = request.client.tenants.create('user/%s' % uid)

    userrec = request.client.users.create(uid,
            apikey, '', tenant_id=tenantrec.id)

    return template('userinfo.html',
            user=userrec,
            tenant=tenantrec,
            apikey=apikey,
            environ=request.environ,
            )


def main():
    opts = parse_args()
    run(host=opts.host, port=int(opts.port))

if __name__ == '__main__':
    main()


