#!/usr/bin/python

import os
import sys
import argparse

from novaclient.v1_1 import client

def parse_args():
    p = argparse.ArgumentParser()
    return p.parse_args()

def main():
    opts = parse_args()
    nc = client.Client(os.environ['OS_USERNAME'], os.environ['OS_PASSWORD'],
            os.environ['OS_TENANT_NAME'], os.environ['OS_AUTH_URL'], service_type="compute")

    return nc

if __name__ == '__main__':
    nc = main()


