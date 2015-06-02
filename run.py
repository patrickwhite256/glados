#!/usr/bin/env python

import signal
import sys

from client import GladosClient

gclient = None


def stop(signum, frame):
    gclient.close()

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, stop)
    try:
        token_file = open('.slack-token')
        token = token_file.read().strip()
    except:
        print('Could not find slack token file .slack-token')
        sys.exit(1)
    gclient = GladosClient(token)
    gclient.connect()
    gclient.run_forever()
