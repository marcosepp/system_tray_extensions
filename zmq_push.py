import zmq

ctx = zmq.Context()
sock = ctx.socket(zmq.PUSH)
sock.bind("ipc://salih")

sock.send_string("asasdasdasd")

sock.close()
ctx.term()