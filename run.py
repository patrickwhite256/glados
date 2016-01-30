#!/usr/bin/env python

import os
import signal
import socket
import sys
import traceback
from multiprocessing import Process

from client import GladosClient

SOCKET_FILENAME = './glados_sock'

gclient = None


def stop(signum, frame):
    gclient.close()


def handle_socket_connections(client, sock):
    while True:
        connection, client_addr = sock.accept()
        try:
            data = connection.recv(256).decode('utf8')
            split_data = data.split(':')
            name_len = int(split_data[0])
            message_contents = ''.join(split_data[1:])
            plugin_name = message_contents[:name_len]
            message_data = message_contents[name_len:]
            client.handle_async(plugin_name, message_data)
        except:
            traceback.print_exc()
        finally:
            connection.close()


def main():
    signal.signal(signal.SIGTERM, stop)
    try:
        token_file = open('.slack-token')
        token = token_file.read().strip()
    except:
        print('Could not find slack token file .slack-token')
        sys.exit(1)

    try:
        os.unlink(SOCKET_FILENAME)
    except OSError:
        if os.path.exists(SOCKET_FILENAME):
            raise

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(SOCKET_FILENAME)
    sock.listen(1)

    debug = False
    if len(sys.argv) > 1:
        if len(sys.argv) == 2 and sys.argv[1] == '--debug':
            debug = True
        else:
            print('Usage: {} [--debug]'.format(sys.argv[0]))

    gclient = GladosClient(token, debug=debug)

    socket_process = Process(target=handle_socket_connections, args=(gclient, sock))
    socket_process.start()
    gclient.connect()
    gclient.run_forever()
    # if it gets past here it's crashed

    socket_process.terminate()

if __name__ == '__main__':
    main()
