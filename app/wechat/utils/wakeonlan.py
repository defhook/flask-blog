#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
远程开机
https://github.com/defhook/pywakeonlan
"""

from __future__ import print_function, unicode_literals, absolute_import

import socket
import struct

BROADCAST_IP = '255.255.255.255'
BROADCAST_PORT = 9  # or 7
BROADCAST_PWD = None


def create_magic_packet(macaddress, pwd=None):
    """
    Create a magic packet which can be used for wake on lan using the
    mac address given as a parameter.
    Keyword arguments:
    :arg macaddress: the mac address that should be parsed into a magic
                     packet.
    """
    if len(macaddress) == 12:
        pass
    elif len(macaddress) == 17:
        sep = macaddress[2]
        macaddress = macaddress.replace(sep, '')
    else:
        raise ValueError('Incorrect MAC address format')

    if pwd:
        if len(pwd) != 8 and len(pwd) != 12:
            raise ValueError('password must be 4 bytes or 6 bytes')
    else:
        pwd = ''

    # Pad the synchronization stream
    data = ''.join(('FFFFFFFFFFFF', macaddress * 16, pwd))
    send_data = b''

    # Split up the hex values in pack
    for i in range(0, len(data), 2):
        send_data += struct.pack(b'B', int(data[i: i + 2], 16))
    return send_data


def send_magic_packet(*macs, **kwargs):
    """
    Wakes the computer with the given mac address if wake on lan is
    enabled on that host.
    Keyword arguments:
    :arguments macs: One or more macaddresses of machines to wake.
    :key ip: the ip address of the host to send the magic packet
                     to (default "255.255.255.255")
    :key port: the port of the host to send the magic packet to
               (default 9)
    :key pwd: the password of the host to send the magic packet to
               (default None)
    """
    packets = []
    ip = kwargs.pop('ip', BROADCAST_IP)
    port = kwargs.pop('port', BROADCAST_PORT)
    pwd = kwargs.pop('pwd', BROADCAST_PWD)
    for k in kwargs:
        raise TypeError('send_magic_packet() got an unexpected keyword '
                        'argument {!r}'.format(k))

    for mac in macs:
        packet = create_magic_packet(mac, pwd)
        packets.append(packet)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    ports = {7, 9}
    ports.add(port)
    for packet in packets:
        for p in ports:
            sock.sendto(packet, (ip, p))
    sock.close()
