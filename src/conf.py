import os
import socket

ip_address = socket.gethostbyname(socket.gethostname())
port = 49153
length_header = 64

log_dir = os.path.join(os.path.expanduser('~'), "log", "lsl-epoching")
data_dir = os.path.join(os.path.expanduser('~'), "Documents", "eeg", "epochs")
data_fname = "epochs.txt"
    
name_marker_stream = "scab-c"
#name_eeg_stream = "BrainAmpSeries"
name_eeg_stream = "jarvis-erp"

icom_clients = None

channels = ["F3", "Fz", "F4", "C3", "Cz", "C4", "P3", "Pz", "P4"]

markers = dict()
markers['nontarget'] = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']
markers['target'] = ['101', '102', '103', '104', '105', '106', '107', '108', '109', '110', '111', '112', '113', '114', '115'] 
markers['trial-start'] = ['200', '201', '202', '203', '204', '205', '206', '207', '208', '209', '210', '211', '212', '213', '214', '215']
markers['trial-end'] = ['255']

#markers = dict()
#markers['new-trial'] = ['200']
#markers['target'] = ['11']
#markers['nontarget'] = ['1']
#markers['end'] = ['255']

#markers_to_epoch = markers['nontarget'] + markers['target']
markers_to_epoch = list()
for m in range(1, 200):
    markers_to_epoch.append(str(m))

#markers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '101', '102', '103', '104', '105', '106', '107', '108', '109']

# length of the buffer in seconds
length_buffer = 10