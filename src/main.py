import os

import socket
import threading
import datetime
import logging
import json

import numpy as np

import pyicom as icom

import acquisition

from utils import log
from pylsl import StreamInlet, resolve_stream, resolve_streams

from utils.std import mkdir

#def eeg_format_convert(data):
#    return np.transpose(data)

def get_ch_names_LSL(inlet):

    ch_names = list()

    info = inlet.info()
    ch = info.desc().child("channels").child("channel")
    for k in range(info.channel_count()):
        ch_names.append(ch.child_value('label'))
        ch = ch.next_sibling()
    
    return ch_names

def conns_send(conns, data):
    logger = logging.getLogger(__name__)
    idx_conn_remove = list()
    for idx, conn in enumerate(conns):
        try:
            conn.send(data)
        except Exception as e:
            #logger.debug("")
            idx_conn_remove.append(idx)
    if len(idx_conn_remove) != 0:
        for m in sorted(idx_conn_remove, reverse=True):
            conns.pop(m)
        logger.debug("some lost connection was closed.")


def main(icom_server,
         icom_clients,
         length_header,
         length_buffer,
         name_marker_stream,
         name_eeg_stream,
         channels,
         markers,
         tmin,
         tmax,
         filter_freq,
         filter_order,
         markers_new_trial,
         markers_end_trial,
         data_dir,
         data_fname):

    logger = logging.getLogger(__name__)
    mkdir(data_dir)
    file_data = open(os.path.join(data_dir, data_fname), 'w')

    logger.debug("channels for acquisition: %s"%str(channels))

    # ------------------------------------------------------------------------------------------------
    # find/connect eeg outlet
    logger.debug("looking for an EEG stream...")
    is_searching = True
    while is_searching:
        streams = resolve_streams(wait_time = 1)
        for stream in streams:
            if stream.name() == name_eeg_stream:
                eeg_inlet = StreamInlet(stream, recover = True)
                fs = stream.nominal_srate()
                logger.debug("EEG Stream : %s" %stream.name())
                is_searching = False

    # create a new inlet to read from the stream
    ch_names = get_ch_names_LSL(eeg_inlet)
    logger.debug("ch_names_LSL : %s" %str(ch_names))
    
    for ch in channels:
        if not ch in ch_names:
            logger.error("channel '%s' is not in LSL EEG stream."%(ch))

    channels_to_acquire = list()
    for idx, ch in enumerate(ch_names):
        if ch in channels:
            channels_to_acquire.append(idx)
    channels_to_acquire = np.array(channels_to_acquire)
    logger.debug("channels_to_acquire (idx) : %s" %str(channels_to_acquire))
    logger.debug("channels_to_acquire : %s" %str(np.array(ch_names)[channels_to_acquire]))

    n_ch = len(channels_to_acquire)
    logger.debug("n_ch for online session : %d" %n_ch)

    # ------------------------------------------------------------------------------------------------
    # find/connect marker outlet

    logger.debug("looking for a marker stream...")
    
    is_searching = True
    while is_searching:
        streams = resolve_streams(wait_time = 1)
        for stream in streams:
            if stream.name() == name_marker_stream:
                marker_inlet = StreamInlet(stream, recover = True)
                logger.debug("Marker Stream : %s" %stream.name())
                is_searching = False

    logger.debug("Configuration was Done.")  
    
    epochs = acquisition.Epochs(n_ch,
                                fs,
                                markers,
                                tmin,
                                tmax,
                                baseline=None,
                                ch_names = channels,
                                ch_types = 'eeg',
                                file_data=file_data,
                                icom_server=icom_server)
    
    acq = acquisition.OnlineDataAcquire(epochs,
                                        eeg_inlet,
                                        channels_to_acquire,
                                        length_buffer,
                                        n_ch,
                                        fs,
                                        marker_inlet,
                                        filter_freq,
                                        filter_order,
                                        new_trial_markers = markers_new_trial,
                                        end_markers = markers_end_trial)
    
    acq.start()
    
    import time
    while True:
        time.sleep(1)
        try:
            pass
        except KeyboardInterrupt:
            break
        #json_data = dict()
        #@json_data['type'] = 'info'
        #json_data['info'] = 'trial-start'
        #json_data['data'] = marker_new_trial
        #server.send(data = json.dumps(json_data).encode('utf-8'))
    file_data.close()
    print("terminate")
    
"""
def server(ip, port, conns):
    logger = logging.getLogger(__name__)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((conf.ip_address, conf.port))
    print("server info. ip: %s, port: %s"%(str(conf.ip_address), str(conf.port)))
    
    #server.settimeout(10)
    while True:
        server.listen()
        conn, addr = server.accept()
        conns.append(conn)
        #print("connected : %s" %str(addr))
        logger.debug("New socket connection was established. '%s'"%str(addr))
"""


if __name__ == "__main__":

    import conf
    log_dir = os.path.join(os.path.expanduser('~'), "log", "lsl-epoching")

    log_strftime = "%y-%m-%d"
    datestr =  datetime.datetime.now().strftime(log_strftime) 
    log_fname = "%s.log"%datestr
    
    print(log_dir)

    mkdir(log_dir)
    if os.path.exists(os.path.join(conf.log_dir, log_fname)):
        os.remove(os.path.join(conf.log_dir, log_fname))
    log.set_logger(os.path.join(log_dir, log_fname), True)
    
    logger = logging.getLogger(__name__)
    logger.debug("ip address: %s"%str(conf.ip_address))
    logger.debug("port: %s"%str(conf.port))
    
    #conns = list()
    #thread = threading.Thread(target=server, args=(conf.ip_address, conf.port, conns))
    #thread.start()
    
    server = icom.server(ip = conf.ip_address,
                         port = conf.port)
    server.start()
    
    main(icom_server=server,
         icom_clients=conf.icom_clients,
         length_header=conf.length_header,
         name_marker_stream = conf.name_marker_stream, 
         name_eeg_stream = conf.name_eeg_stream,
         channels = conf.channels,
         markers = conf.markers_to_epoch,
         length_buffer=conf.length_buffer,
         tmin = -0.1,
         tmax = 1,
         filter_freq = [1, 40],
         #filter_freq = None,
         filter_order = 2,
         markers_new_trial = conf.markers['trial-start'],
         markers_end_trial = conf.markers['trial-end'],
         data_dir=conf.data_dir,
         data_fname=conf.data_fname)