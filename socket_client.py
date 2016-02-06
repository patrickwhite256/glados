#!/usr/bin/env python
import argparse
import socket
import sys

SOCKET_FILENAME = './glados_sock'


def main():
    parser = argparse.ArgumentParser(description='Send data to GLaDOS')

    parser.add_argument('--plugin', dest='plugin_name',
                        help='Plugin to send the data to', required=True)
    parser.add_argument('--data', dest='data',
                        help='Data to send to the plugin. '
                        'If not provided will accept from stdin.')
    parser.add_argument('--no-data', dest='no_data', action='store_true',
                        help='Send no data to the plugin (overrides --data).')

    args = parser.parse_args()

    if args.no_data:
        message_data = ''
    elif args.data:
        message_data = args.data
    else:
        message_data = ""
        for line in sys.stdin:
            message_data += line

    message_contents = '{}:{}{}'.format(len(args.plugin_name),
                                        args.plugin_name, message_data)

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    sock.connect(SOCKET_FILENAME)
    sock.sendall(message_contents.encode('utf8'))
    sock.close()

if __name__ == '__main__':
    main()
