import sys
import time
import traceback
import threading
import copy
import json
from logging import getLogger
import numpy as np
from scipy import signal

def pop_list_indexes(list, indexes_to_remove):
    list = copy.copy(list)
    indexes_to_remove = copy.copy(indexes_to_remove)
    for index in sorted(indexes_to_remove, reverse=True):
        list.pop(index)
    return list

class DataStruct:
    data = np.array([])
    time = np.array([])
    data_chunk = list()
    time_chunk = list()
    time_correction = list()

class OnlineDataAcquire(object):

    def __init__(
            self,
            epochs,
            eeg_inlet,
            channels_to_acquire,
            length_buffer = 10,
            nch_eeg=None,
            fs_eeg=None,
            marker_inlet=None,
            filter_freq=None,
            filter_order=None,
            format_convert_eeg_func=None,
            format_convert_marker_func=None):

        logger = getLogger(__name__)
        self.epochs = epochs
        self.eeg_inlet = eeg_inlet
        self.nch_eeg = nch_eeg
        self.fs_eeg = fs_eeg
        self.z = None
        self.marker_inlet = marker_inlet
        self.filter_freq = filter_freq
        self.filter_order = filter_order
        self.format_convert_eeg_func = format_convert_eeg_func
        self.format_convert_marker_func = format_convert_marker_func
        
        self.length_buffer = length_buffer

        self.channels_to_acquire = channels_to_acquire
        if type(channels_to_acquire) == list:
            self.channels_to_acquire = np.array(self.channels_to_acquire)

        self.is_running = False

        logger.debug("Online Data Aquire module was initialized.")

    def start(self):
        logger = getLogger(__name__)
        logger.debug("Online Data Acquire module was started.")
        self.is_running = True
        self.thread = threading.Thread(target=self.main_thread)
        self.thread.start()

    def stop(self):
        logger = getLogger(__name__)
        logger.debug("Online Data Acquire module was stopped.")
        self.is_running = False

    def main_thread(self):
        logger = getLogger(__name__)

        # ------------------------------------------------------------------------------------------------
        # online filter
        if self.filter_freq is not None:
            sos = signal.butter(self.filter_order, np.array(self.filter_freq)/(self.fs_eeg/2), 'bandpass', output='sos')
            self.z = np.zeros((self.filter_order, self.nch_eeg, 2))
            # Shape of initial Z should be (filter_order, number_of_eeg_channel, 2)
            # or
            # z = signal.sosfilt_zi(sos) # shape of the returned object will be (filter_order, 2)
            logger.debug("Filter cofficients were derived.")

        # ------------------------------------------------------------------------------------------------

        eeg = DataStruct()
        eeg.data = np.empty((self.nch_eeg, 0))

        marker = DataStruct()
        marker.data = np.empty((0), dtype=np.int64)

        #Epoch = data_structure.Epoch(n_ch, fs_eeg, MARKERS_TO_EPOCH, EPOCH_RANGE, EPOCH_BASELINE)
        # 'epochs' is passed from parent
        self.epochs.set(eeg, marker) # push by reference

        logger.debug("start receiving data.")
        try:
            while self.is_running:
                try:
                    eeg.data_chunk, eeg.time_chunk = self.eeg_inlet.pull_chunk()
                    marker.data_chunk, marker.time_chunk = self.marker_inlet.pull_chunk()
                    #eeg.time_correction = self.eeg_inlet.time_correction()
                    #marker.time_correction = self.marker_inlet.time_correction()
                except Exception as e:
                    from pylsl.pylsl import LostError
                    if type(e) == LostError:
                        logger.error("Error : \n%s" %(traceback.format_exc()))
                        break

                if eeg.time_chunk:
                    
                    # has shape of (n_samples, n_ch)
                    eeg.data_chunk = np.array(eeg.data_chunk) 

                    # now it's shape of (n_ch, n_samples)
                    eeg.data_chunk = np.transpose(eeg.data_chunk) 

                    # pick selected channels
                    eeg.data_chunk = eeg.data_chunk[self.channels_to_acquire, :]

                    # apply filter
                    if self.filter_freq is not None:
                        eeg.data_chunk, self.z = signal.sosfilt(sos, eeg.data_chunk, axis=1, zi=self.z)

                    # concatenate data
                    time_start = time.perf_counter()
                    eeg.data = np.concatenate((eeg.data, eeg.data_chunk), axis=1)
                    time_end = time.perf_counter()
                    #logger.debug("concanating eeg.data and eeg.data_chunk took %.5f seconds"%(time_end - time_start))

                    # append time
                    eeg.time = np.append(eeg.time, eeg.time_chunk)       

                    self.epochs.update()
                    
                    # keep the buffer size
                    _, Ns = eeg.data.shape
                    if Ns > self.length_buffer*self.fs_eeg:
                        eeg.data = eeg.data[:, int(Ns-(self.length_buffer*self.fs_eeg)):Ns]
                        eeg.time = eeg.time[int(Ns-(self.length_buffer*self.fs_eeg)):Ns]
                        


                if marker.time_chunk:

                    logger.debug("markers '%s' was recieved"%str(marker.data_chunk))

                    # append marker data and time info
                    time_start = time.perf_counter()
                    marker.data = np.append(marker.data, marker.data_chunk)
                    marker.time = np.append(marker.time, marker.time_chunk)

                    I = np.where(marker.time < eeg.time[0])[0]
                    if len(I) > 0:
                        marker.time = np.delete(marker.time, I)
                        marker.data = np.delete(marker.data, I)
                    #logger.debug("I: %s"%str(I))
                    #logger.debug("marker.data: %s"%str(marker.data))

                    time_end = time.perf_counter()
                    
                    self.epochs.update(marker_data_chunk = marker.data_chunk, marker_time_chunk = marker.time_chunk)
        except:
            logger.error("Error : \n%s" %(traceback.format_exc()))

        logger.debug("stop receiving data.")
        

class Epochs():
    def __init__(self,
                 n_ch,
                 fs,
                 markers_to_epoch,
                 tmin,
                 tmax,
                 callback,
                 data_callback = None,
                 baseline=None,
                 ch_names=None,
                 ch_types='eeg',
                 #file_data=None,
                 icom_server=None):
        """
        Parameters
        ----------
        n_ch : number of EEG channels
        markers_to_epoch : markers to epoch e.g. [1,3,5]
        range : epoching range relative to marker onset e.g. [-0.1 1.0]
        baseline : NOT IMPLEMENTED!!!! range of baseline correction. if pass None, baseline correction will not be applied
        """
        self.n_ch = n_ch
        self.fs = fs
        self.markers_to_epoch = markers_to_epoch
        self.tmin = tmin
        self.tmax = tmax
        self.callback = callback
        self.data_callback = data_callback
        self.baseline = baseline
        #self.file_data = file_data
        self.icom_server = icom_server

        self.data = None
        self.events = None

        self.length_epoch = np.floor(fs*(self.tmax-self.tmin)).astype(np.int64)+1
        
        self.eeg = None
        self.marker = None
        
        self.events_list = list()
        self.time_list = list()
        
        self.epoched_time_list = list()

        self.epochs = dict()
        self.events = dict()

        if self.baseline is not None:
            raise ValueError("baseline correction is not currently implemented. set baseline = None")


    def set(self, eeg, marker):
        self.eeg = eeg
        self.marker = marker

    def update(self, marker_data_chunk = None, marker_time_chunk = None):

        logger = getLogger(__name__)
        
        # check if the marker is in the self.markers_to_epoch
        if marker_data_chunk is not None and marker_time_chunk is not None:
            for data, time_marker in zip(np.array(marker_data_chunk), np.array(marker_time_chunk)):
                # data in self.markers_to_epoch: check if the marker is needed to be epoched
                # time_marker > self.time_list[-1]: check if the marker is latest (updated in OnlineDataAcquire). Other wise, the already epoched marker will be added
                if data in self.markers_to_epoch:
                        self.events_list.append(data[0])
                        self.time_list.append(time_marker)
            #logger.debug("self.events_list: %s"%str(self.events_list))
            #logger.debug("self.time_list: %s"%str(self.time_list))
        
        
        # epoching
        
        #logger.debug("self.time_list: %s"%(str(self.time_list)))
        idx_to_delete = list()
        for idx, (time_marker, events) in enumerate(zip(self.time_list, self.events_list)):
            if (self.eeg.time[-1] > (time_marker + self.tmax + 5/self.fs)):
                idx_start = int(np.argmin(np.absolute(self.eeg.time - (time_marker + self.tmin))))
                idx_end = int(idx_start + self.length_epoch)

                diff = np.min(np.absolute(self.eeg.time - (time_marker + self.tmin)))
                if diff > (10/self.fs):
                    logger.error("Marker: %s, Difference between eeg and marker is %.5f sec. There may be synchronization error."%(str(events), diff))

                epochs = self.eeg.data[:, idx_start:idx_end]
                
                self.callback(epochs = epochs, events = events, data = self.data_callback)
                logger.debug("Epoch for '%s' was acquired"%(str(events)))
                
                idx_to_delete.append(idx)

        if len(idx_to_delete) > 0:
            #logger.debug("self.events_list: %s"%(str(self.events_list)))
            #logger.debug("idx_to_delete: %s"%(str(idx_to_delete)))
            self.time_list = pop_list_indexes(self.time_list, idx_to_delete)
            self.events_list = pop_list_indexes(self.events_list, idx_to_delete)
            #logger.debug("self.events_list (after): %s"%(str(self.events_list)))