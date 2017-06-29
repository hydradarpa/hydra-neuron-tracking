import pandas as pd
import numpy as np
import csv

def eucl(x, y):
    return np.linalg.norm(np.asarray(x)-np.asarray(y))

def load_files(paths):
    vid = []
    for path in paths:
        vid.extend(load_file(path))
    print 'video loaded'
    return vid

def load_file(path):
    df = pd.read_csv(path)
    vid = []
    frame_count = int(np.nanmax(np.asarray(df['t']) + 1))
    for i in range(frame_count):
        frame = df[df.t == i]
        coords = frame[['x', 'y', 'Surface', 'average intensity', 'max intensity']]
        tuples = [tuple(x) for x in coords.values]
        if len(tuples) != 0:
            vid.append(np.asarray(tuples))
    print 'loaded %d frames' % len(vid)
    return vid

# writes neuron assignment structure as csv file
def write_neuron_assignments(neurons, path):
	with open(path, 'wb') as csv_file:
	    writer = csv.writer(csv_file)
	    for i in range(len(neurons)):
	        keys = sorted(neurons[i].keys())
	        for j in keys:
	            writer.writerow([i, j, neurons[i][j][0], neurons[i][j][1]])

# reads in csv file as neuron assignment structure
def load_neuron_assignments(path):
	df = pd.read_csv(path)
	neurons = []
	neuron_count = int(np.nanmax(np.asarray(df.neuron) + 1))
	for i in range(neuron_count):
	    track = df[df.neuron == i]
	    time_count = int(np.nanmax(np.asarray(track.time) + 1))
	    time_map = {}
	    for j in range(time_count):
	        frame = track[track.time == j]
	        coords = frame[['x', 'y']]
	        tuples = [tuple(x) for x in coords.values]
	        time_map[j] = np.asarray(tuples[0])
	    neurons.append(time_map)
	return neurons