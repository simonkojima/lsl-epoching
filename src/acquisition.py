import sys
import time
import traceback
import threading
import copy
from logging import getLogger
import numpy as np
from scipy import signal


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
            nch_eeg=None,
            fs_eeg=None,
            marker_inlet=None,
            filter_freq=None,
            filter_order=None,
            format_convert_eeg_func=None,
            format_convert_marker_func=None,
            new_trial_markers=None,
            end_markers=None):

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

        self.channels_to_acquire = channels_to_acquire
        if type(channels_to_acquire) == list:
            self.channels_to_acquire = np.array(self.channels_to_acquire)

        self.new_trial_markers = new_trial_markers
        if type(new_trial_markers) == int:
            self.new_trial_markers = list(self.new_trial_markers)

        self.end_markers = end_markers
        if type(self.end_markers) == int:
            self.end_markers = list(self.end_markers)

        self.is_running = False

        self.got_new_trial_marker = False
        self.got_end_marker = False
        self.trial_was_end = False

        logger.debug("Online Data Aquire module was initialized.")

    def start(self):
        logger = getLogger(__name__)
        logger.debug("Online Data Acquire module was started.")
        self.thread = threading.Thread(target=self.main_thread)
        self.is_running = True
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
                    eeg.time_correction = self.eeg_inlet.time_correction()
                    marker.time_correction = self.marker_inlet.time_correction()
                except Exception as e:
                    from pylsl.pylsl import LostError
                    if type(e) == LostError:
                        logger.error("Error : \n%s" %(traceback.format_exc()))
                        break

                if eeg.time_chunk:                
                    self.epochs.update()
                    

                if marker.time_chunk:
                    logger.debug("markers '%s' was recieved"%str(marker.data_chunk))
                    self.epochs.update()
        except:
            logger.error("Error : \n%s" %(traceback.format_exc()))

        logger.debug("stop receiving data.")

    def get_marker_data(self):
        return self.marker

    def is_trial_end(self):
        if self.trial_was_end:
            self.trial_was_end = False
            return True

    def is_got_new_trial_marker(self):
        if self.got_new_trial_marker != False:
            marker = self.got_new_trial_marker
            self.got_new_trial_marker = False
            return marker
        else:
            return False
        

class Epochs():
    def __init__(self, n_ch, fs, markers_to_epoch, tmin, tmax, baseline=None, ch_names=None, ch_types='eeg'):
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
        #range_epoch = [tmin, tmax]
        self.range_epoch = [tmin, tmax]
        self.baseline = baseline
        self.data = None
        self.events = None
        self.ch_types = ch_types
        if ch_names == None:
            self.ch_names = list()
            for m in range(n_ch):
                self.ch_names.append("ch" + str(m+1))
        else:
            self.ch_names = ch_names
        #self.info = mne.create_info(self.ch_names, self.fs, ch_types=self.ch_types)

        self.length_epoch = np.floor(fs*(self.range_epoch[1]-self.range_epoch[0])).astype(np.int64)+1
        
        self.eeg = None
        self.marker = None

        self.epochs = dict()
        self.events = dict()
        self.n_markers = None # total markers in trial
        self.n_epoched = None # total epochs acquired

        #self.event_epoching = list() # event and time_sample for epoching.
        
        self.new_epochs_idx = list()
        self.epoched_idx = list()
        
        #self.epoched_marker = list()

        #self.new_data = np.array([], dtype=np.int64)


    def set(self, eeg, marker):
        self.eeg = eeg
        self.marker = marker
        
        #self.epoched_marker = np.zeros((len(marker.data)), dtype=np.int64)

    def clear(self):
        self.epochs = dict()
        self.events = dict()

        self.n_markers = None
        self.n_epoched = None
        
        self.new_epochs_idx = list()
        self.epoched_idx = list()

    def update(self):

        logger = getLogger(__name__)
        #time.sleep(0.1)

        if self.marker.data.size == 0:
            # don't process if there's no markers received.
            return
        

        # check if the marker is in the self.markers_to_epoch
        idx_to_delete = list()
        for idx, val in enumerate(np.unique(self.marker.data)):
            if (val in self.markers_to_epoch) is False:
                I = np.where(self.marker.data == val)
                for i in I:
                    idx_to_delete += i.tolist()
        self.marker.data = np.delete(self.marker.data, idx_to_delete)
        self.marker.time = np.delete(self.marker.time, idx_to_delete)
        
        self.n_markers = len(self.marker.time)

        # check if the marker can be epoched
        for idx, time_marker in enumerate(self.marker.time):
            #eeg_end_time = self.eeg.time[-1]
            if (self.eeg.time[-1] > (time_marker + self.tmax + 5/self.fs)) and ((idx in self.epoched_idx) is False):
                idx_start = int(np.argmin(np.absolute(self.eeg.time - (time_marker + self.tmin))))
                idx_end = int(idx_start + self.length_epoch)
                #idx_end = idx_start + self.length_epoch
                if (idx_end - idx_start) != self.length_epoch:
                    raise ValueError("length_epoch is invalid")
                self.epochs[idx] = self.eeg.data[:, idx_start:idx_end]
                self.events[idx] = self.marker.data[idx]
                self.new_epochs_idx.append(idx)
                self.epoched_idx.append(idx)
                 
        self.n_epoched = len(self.epochs)

    def get_data(self):
        if len(self.epochs) == 0:
            return None
        else:
            return self.epochs
    
    def has_new_data(self):
        if len(self.new_epochs_idx) == 0:
            return False
        else:
            return True
    
    def get_new_data(self):
        if self.has_new_data() == False:
            return None
        else:
            
            # sometimes, new epoch is recorded, and self.new_epochs_idx have new index data
            # in for loop below. To prevent this, copy the object.
            new_epochs_idx = copy.copy(self.new_epochs_idx)

            events_new = list()
            epochs_new = np.zeros((len(new_epochs_idx), self.n_ch, self.length_epoch))
            for idx, idx_epochs in enumerate(new_epochs_idx):
                epochs_new[idx, :, :] = self.epochs[idx_epochs]
                events_new.append(self.events[idx_epochs])
            
            for idx_epochs in new_epochs_idx:
                self.new_epochs_idx.remove(idx_epochs)

            return epochs_new, events_new