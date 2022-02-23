import zmq

ctx = zmq.Context()
sock = ctx.socket(zmq.PULL)
sock.connect("ipc://salih")

while True:
    msg = sock.recv_string()
    print("Received string: %s ..." % msg)

sock.close()
ctx.term()