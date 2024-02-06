import socket

IPADDR = "127.0.0.1"
PORT = 49153

cl_1 = socket.socket(socket.AF_INET)
cl_1.connect((IPADDR, PORT))