#!/usr/bin/python

import os
import sys
import string
import random

import bottle
from bottle import route,request,response,redirect

import novaclient.v1_1.client as nova
import novaclient.exceptions
import keystoneclient.exceptions

import static
from apperrors import *
from decorators import render, authenticated

@route('/style.css')
@render('style.css')
def style_css():
    '''Serves up our stylesheet.  This can't be a static file because we
    need to do template subsitution on URL paths.'''
    response.set_header('Content-type', 'text/css')
    return {}

@route('/error/:code')
@render('error.html')
def error(code):
    '''This meant to be used with Apache `ErrorDocument` directives.'''
    if code == '401':
        raise AuthenticationRequiredError()
    elif code == '403':
        raise AuthenticationFailedError()
    else:
        raise ApplicationError()

@route('/auth/debug')
@render('debug.html')
def debug():
    '''Dump various internal data to a web page.'''
    if not request.app.config.get('debug'):
        raise DebugModeDisabledError()

    return dict(
            config = request.app.config,
            )

@route('/')
@render('index.html')
def index():
    message = request.query.get('message')
    return dict(
            message=message,
            )

@route('/auth/info')
@render('userinfo.html')
@authenticated
def info():
    uid = request.environ['REMOTE_USER']

    try:
        userrec = request.client.users.find(name=uid)
        tenantrec = request.client.tenants.get(userrec.tenantId)
        return dict(
                user=userrec,
                tenant=tenantrec,
                )
    except keystoneclient.exceptions.NotFound:
        redirect('%s?message=You+do+not+have+a+SEAS+cloud+account.' % (
            request.script_name))

@route('/auth/newkey')
@render('userinfo.html')
@authenticated
def newkey():
    '''Generate a new password for the authenticated user if they have
    an existing OpenStack account.'''

    uid = request.environ['REMOTE_USER']
    passwd = ''.join(random.sample(string.letters + string.digits,
            20))
    try:
        userrec = request.client.users.find(name=uid)
        tenantrec = request.client.tenants.get(userrec.tenantId)
    except keystoneclient.exceptions.NotFound:
        redirect('%s?message=You+do+not+have+a+SEAS+cloud+account.' % (
            request.script_name))

    request.client.users.update_password(userrec.id, passwd)
    return dict(
            user=userrec,
            tenant=tenantrec,
            passwd=passwd,
            )

def create_security_rules(group, rules):
    '''Apply security rules from 'rules' to 'group'
    security group.'''

    for rule in rules:
        try:
            sr = nc.security_group_rules.create(
                    group.id,
                    ip_protocol=rule['protocol'],
                    from_port=rule['from port'],
                    to_port=rule['to port'])
        except novaclient.exceptions.BadRequest:
            # This probably means that the rule already exists.
            pass

def create_security_groups():
    for name in request.config.get('security groups', []):
        try:
            group = request.nc.security_groups.find(name=name)
        except novaclient.exceptions.NotFound:
            group = request.nc.security_groups.create(
                    name, '%s security group' % name)

        create_security_group_rules(
                group,
                request.config['security groups'][name])

@route('/auth/create')
@render('userinfo.html')
@authenticated
def create():
    '''Create a new OpenStack user, including the following:

    - Create a new tenant named "user/<username>".
    - Create a new user account.
    - Populate the "default" security group for the tenant.
    '''
    uid = request.environ['REMOTE_USER']
    passwd = ''.join(random.sample(string.letters + string.digits,
            20))

    # Does the user exist?
    try:
        userrec = request.client.users.find(name=uid)
    except keystoneclient.exceptions.NotFound:
        userrec = None

    # If the user already exists, just display account information.
    if userrec:
        redirect('%sauth/info' % request.script_name)

    # If we get this far we need to create the user.  First
    # see if the appropriate tenant already exists (which might
    # happen if someone deletes the user via the gui and leaves the tenant
    # in place).
    try:
        tenantrec = request.client.tenants.find(name='user/%s' % uid)
    except keystoneclient.exceptions.NotFound:
        tenantrec = request.client.tenants.create('user/%s' % uid)

    userrec = request.client.users.create(uid,
            passwd, '', tenant_id=tenantrec.id)

    # Create security groups.
    request.nc = nova.Client(userrec.name, passwd, tenantrec.name,
            request.app.config.service_endpoint,
            service_type='compute')

    create_security_groups()

    return dict(
            user=userrec,
            tenant=tenantrec,
            passwd=passwd,
            message='Your SEAS Cloud account is ready.',
            )

