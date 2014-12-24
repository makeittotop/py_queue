#!/usr/bin/env python

import sys
import zmq
import os
import logging
from daemonize import Daemonize
import time
import subprocess

pid = "/tmp/run/notification_client.pid"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
fh = logging.FileHandler("/tmp/log/notification_client.log", "w")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
keep_fds = [fh.stream.fileno()]

def main():
    port = "8888"

    # Socket to talk to server
    context = zmq.Context()
    socket = context.socket(zmq.SUB)

    socket.connect ("tcp://172.16.15.246:%s" % port)

    topicfilter = "all"
    socket.setsockopt(zmq.SUBSCRIBE, topicfilter)

    logger.debug("Waiting for server broadcasts ...")

    while True:
        string = socket.recv()
        topic, messagedata = string.split()
        messagedata = " ".join(messagedata.split("_"))

        #print >>sys.stderr, "{0}: {1}".format(topic, messagedata)
        logger.debug("{0}: {1}".format(topic, messagedata))
        #notify-send --urgency=critical --expire-time=0 -i /usr/share/icons/gnome/32x32/apps/ksysguard.png Alert foo
        #os.system("DISPLAY=:0.0;notify-send --urgency=critical --expire-time=0 --icon=/usr/share/icons/gnome/32x32/apps/ksysguard.png 'Alert' {0}".format(messagedata))
        subprocess.call('DISPLAY=:0 notify-send --urgency=critical --expire-time=0 --icon=/usr/share/icons/gnome/32x32/apps/ksysguard.png "Alert" {0}'.format(messagedata), shell=True)

        '''
        n = pynotify.Notification("Attention", messagedata, "dialog-warning")
        n.set_urgency(pynotify.URGENCY_NORMAL)
        n.set_timeout(pynotify.EXPIRES_NEVER)
        #n.add_action("clicked","Button text", callback_function, None)
        try:
            n.show()
        except:
            n.show()
        '''    
main()
#daemon = Daemonize(app="notification_client", pid=pid, action=main, keep_fds=keep_fds)
#daemon.start()
