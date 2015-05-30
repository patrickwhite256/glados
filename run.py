#!/usr/bin/env python

import multiprocessing
import signal

from client import GladosClient

gclient = None

def stop(signum, frame):
    gclient.close()

signal.signal(signal.SIGTERM, stop)

if __name__ == '__main__':
    gclient = GladosClient()
    gclient.connect()
    gclient.run_forever()
