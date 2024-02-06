import os
import socket

ip_address = socket.gethostbyname(socket.gethostname())
port = 49152
length_header = 64

log_dir = os.path.join(os.path.expanduser('~'), "log", "lsl-epoching")
    
marker_stream_name = "MyMarkerStream"
channels = ["F3", "Fz", "F4", "C3", "Cz", "C4", "P3", "Pz", "P4"]

markers = dict()
markers['nontarget'] = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
markers['target'] = ['101', '102', '103', '104', '105', '106', '107', '108', '109'] 
markers['new-trial'] = ['201', '202', '203', '204', '205', '206', '207', '208', '209']
markers['end'] = ['255']

markers_to_epoch = markers['nontarget'] + markers['target']

#markers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '101', '102', '103', '104', '105', '106', '107', '108', '109']