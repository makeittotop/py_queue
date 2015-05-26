import zerorpc
import sys

c = zerorpc.Client()
c.connect("tcp://16.16.16.2:4242")
#print c.hello("RPC")

print c.cancel_pending_task(sys.argv[1])
print c.cancel_running_task(sys.argv[1])
