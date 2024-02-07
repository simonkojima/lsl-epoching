import os
import json

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

with open("oddball.json", 'r') as f:
    data = json.load(f)

events = list()
for event in data['events']:
    events += event

epochs = list()
for epoch in data['epochs']:
    epochs += epoch
epochs = np.array(epochs)

print(len(events))
print(epochs.shape)

idx_target = np.where(np.array(events) == '11')[0]
idx_nontarget = np.where(np.array(events) == '1')[0]
print(idx_target)
print(idx_nontarget)

target = np.mean(epochs[idx_target, :, :], axis=0)
nontarget = np.mean(epochs[idx_nontarget, :, :], axis=0)
print(target.shape)

sns.set()
plt.plot(target[0,:])
plt.plot(nontarget[0,:])
plt.show()