#!/usr/bin/env python

import zmq
import sys
import os

if len(sys.argv) != 3:
    print >>sys.stderr, "Usage: script <to> <message>"
    sys.exit(0)

p_port = "8887"

context = zmq.Context()
p_socket = context.socket(zmq.PAIR)
p_socket.connect("tcp://172.16.15.246:%s" % p_port)

body = "_".join(sys.argv[2].split())
message = "{0} {1}".format(sys.argv[1], body)

print >>sys.stderr, "Sending message: {0} to the server to broadcast ...".format(message)

p_socket.send(message)
