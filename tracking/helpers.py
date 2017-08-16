import pandas as pd
import numpy as np
import csv

# euclidean distance of vectors
def eucl(x, y):
    return np.linalg.norm(np.asarray(x)-np.asarray(y))

# load files in the ICY detections schema, consistent with motion correction pipeline
# input: array of csv path names
# output: full_spots[index] is array of all spots in frame at time index
def load_files(paths):
    vid = []
    for path in paths:
        vid.extend(load_file(path))
    print 'video loaded'
    return vid

# load individual csv file and return full_spots subarray, concatenated into full array
# input: csv path name of icy spot detections
# output: full_spots[index] is array of all spots in frame at time index
def load_file(path):
    df = pd.read_csv(path)
    vid = []
    frame_count = int(np.nanmax(np.asarray(df['Position T']) + 1))
    for i in range(frame_count):
        frame = df[df['Position T'] == i]
        coords = frame[['Position X', 'Position Y', 'Area (m2)', 'Max Intensity (ch 0)']]
        tuples = [tuple(x) for x in coords.values]
        if len(tuples) != 0:
            vid.append(np.asarray(tuples))
    print 'loaded %d frames' % len(vid)
    return vid

# writes neuron assignment structure as csv file
# input: neurons[index] is a map from time to spot profile, save path, resolution, position_only boolean (as opposed to entire spot profile)
def write_neuron_assignments(neurons, path, res, position_only = False):
    with open(path, 'wb') as csv_file:
        writer = csv.writer(csv_file)
        for i in range(len(neurons)):
            keys = sorted(neurons[i].keys())
            for j in keys:
                if position_only:
                    writer.writerow([i, j, res * neurons[i][j][0], res * neurons[i][j][1]])
                else:
                    writer.writerow([i, j, res * neurons[i][j][0], res * neurons[i][j][1], neurons[i][j][2], neurons[i][j][3], neurons[i][j][4]])

# reads in csv file as neuron assignment structure
# input: csv neuron assignment read path
# output: neurons[index] is a map from time to spot profile
def load_neuron_assignments(path):
    df = pd.read_csv(path, header=None)
    neurons = []
    neuron_count = int(np.nanmax(np.asarray(df[df.columns[0]]) + 1))
    for i in range(neuron_count):
        time_map = {}
        track = df[df[df.columns[0]] == i]
        for index, row in track.iterrows():
            time_map[int(row[1])] = np.asarray([row[2], row[3], row[4], row[5], row[6]])
        neurons.append(time_map)
    return neurons