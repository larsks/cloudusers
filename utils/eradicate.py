#!/usr/bin/python

import os
import sys
import argparse
import string
import random

import keystoneclient.v2_0.client as keystone
from keystoneclient.exceptions import *

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--delete-tenant', '-t', action='store_true')
    p.add_argument('uid')
    return p.parse_args()

def main():
    opts = parse_args()
    client = keystone.Client(
            endpoint=os.environ['SERVICE_ENDPOINT'],
            token=os.environ['SERVICE_TOKEN'],
            )

    userrec = client.users.find(name=opts.uid)
    tenantrec = client.tenants.get(userrec.tenantId)

    print 'deleting user %s (%s)' % (userrec.name, userrec.id)
    client.users.delete(userrec.id)
    if opts.delete_tenant:
        print 'deleting tenant %s (%s)' % (tenantrec.name, tenantrec.id)
        client.tenants.delete(tenantrec.id)

if __name__ == '__main__':
    main()


