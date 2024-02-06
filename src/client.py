import socket
import json

SERVER = socket.gethostbyname(socket.gethostname())
IPADDR = "127.0.0.1"
IPADDR = SERVER
PORT = 49152
header = 64
#FORMAT = ''

cl = socket.socket(socket.AF_INET)
cl.connect((IPADDR, PORT))
print("connected.")

while True:
    #cmd = input()
    #cl.send(cmd.encode('utf-8'))
    msg_length = int.from_bytes(cl.recv(header), 'big')
    msg = cl.recv(msg_length).decode('utf-8')
    print(json.loads(msg))
