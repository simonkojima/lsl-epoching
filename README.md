# lsl-epoching


# documentation for conf.py
| item | description |
| ---- | ----------- |
| ip_adderess | ip address of the machine |
| port | port will be used for socket communication |
| length_header | length for sending header infomation. shoule be match with other modules |
| log_dir | base directory for saving log files. |
| name_marker_stream | name of the lsl marker stream to be fetched |
| name_eeg_stream | name of the lsl eeg stream to be fetched |
| channels | channel labels for eeg stream. TODO: fetch it from eeg stream |
| markers | dict() object which has information about each marker, should have following four keys, 'nontarget', 'target', 'trial-start', 'trial-end' |
| markers_to_epoch | The markers which will be epoched should be in this list |


# Communication
## Receive
N/A

## Send
### Start Epoching
type: 'info'
info: 'trial-start'
data: marker which trigger starting a new trial

### Epoch data
type: 'epochs'
epochs: epochs
events: events

epochs has length of number of epochs, 
each epoch data has length of channels,
each channel data has length of time samples.
i.e., np.array(epochs).shape has(number_of_epochs, number_of_channels, number_of _samples)

events has length of epochs.

### Finish epoching
type: 'info'
info: 'trial-end'