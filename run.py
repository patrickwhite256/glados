#!/usr/bin/env python

import sys

from client import GladosClient


def main():
    try:
        token_file = open('.slack-token')
        token = token_file.read().strip()
    except FileNotFoundError:
        print('Could not find slack token file .slack-token')
        sys.exit(1)

    debug = False
    if len(sys.argv) > 1:
        if len(sys.argv) == 2 and sys.argv[1] == '--debug':
            debug = True
        else:
            print('Usage: {} [--debug]'.format(sys.argv[0]))

    gclient = GladosClient(token, debug=debug)

    try:
        gclient.run()
        # if it gets past here it's crashed
    finally:
        gclient.close()

if __name__ == '__main__':
    main()
