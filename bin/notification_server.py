#!/usr/bin/env python

import zmq
import random
import sys
import time

p_port = "8887"
b_port = "8888"

context = zmq.Context()

p_socket = context.socket(zmq.PAIR)
p_socket.bind("tcp://*:%s" % p_port)

b_socket = context.socket(zmq.PUB)
b_socket.bind("tcp://*:%s" % b_port)

while True:
    message = p_socket.recv()

    topic, message = message.split()

    broadcast = "%s %s" % (topic, message)
    print >>sys.stderr, broadcast

    b_socket.send(broadcast)
