import os
import sys

import socket
import json

sys.path.append(os.path.join(os.path.expanduser('~'), "git", "pyerp", "src"))
import pyerp

SERVER = socket.gethostbyname(socket.gethostname())
IPADDR = "127.0.0.1"
IPADDR = SERVER
PORT = 49152
header = 64
#FORMAT = ''

cl = socket.socket(socket.AF_INET)
cl.connect((IPADDR, PORT))
print("connected.")

json_save_dir = os.path.join(os.path.expanduser('~'), "Documents", "eeg", "lsl-online")

epochs = list()
events = list()

json_save = dict()
while True:
    #cmd = input()
    #cl.send(cmd.encode('utf-8'))
    msg_length = int.from_bytes(cl.recv(header), 'little')
    msg = cl.recv(msg_length).decode('utf-8')
    msg_json = json.loads(msg)
    print(list(msg_json.keys()))
    
    if msg_json['type'] == 'epochs':
        epochs.append(msg_json['epochs'])
        events.append(msg_json['events'])
        json_save['epochs'] = epochs
        json_save['events'] = events
        #pyerp.utils.save_json(os.path.join(json_save_dir, "oddball.json"), json_save)
        
    if msg_json['type'] == 'info':
        if msg_json['info'] == 'end-trial':
            pyerp.utils.save_json(os.path.join(json_save_dir, "oddball.json"), json_save)
        
    
        

    

    
    
