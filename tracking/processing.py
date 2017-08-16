import pandas as pd
import numpy as np
import copy
import csv

import helpers

# read correction map structure from csv
# input: correction map read path
# output: map[original correction space coordinates] is coordinates of spot in original video space
def load_correction_map(path):
    df = pd.read_csv(path)
    frame_count = int(np.nanmax(np.asarray(df['t']) + 1))
    res = [{} for _ in xrange(frame_count + 1)]
    for i in range(frame_count):
        frame = df[df['t'] == i]
        mapping = frame[['x', 'y', 'x_corrected', 'y_corrected']]
        for row in mapping.itertuples():
            res[i][(round(row[3]), round(row[4]))] = (row[1], row[2])
    return res

# map neuron tracks in motion corrected space back to corresponding tracks in original video space
# input: neuron tracks structure in motion corrected space, correction_map[original correction space coordinates] is coordinates of spot in original video space
# output: neuron tracks structure in original video space
# TODO: arbitrary euclidean distance cut-off of 2 pixels in matching to closest point
def reverse_correction(neurons, correction_map):
    corrected_map = [{} for _ in xrange(len(neurons))]
    for n in range(len(neurons)):
        neuron = neurons[n]
        for time in neuron.keys():
            new_res = copy.copy(neuron[time])
            
            dists = list(map(lambda x: helpers.eucl(x, (new_res[0], new_res[1])), correction_map[time].keys()))
            
            if min(dists) < 2:
                index = dists.index(min(dists))
                match = correction_map[time].keys()[index]
                new_res[0] = correction_map[time][match][0]
                new_res[1] = correction_map[time][match][1]
                corrected_map[n][time] = new_res
    return corrected_map

# processes time assignments to construct neuron tracks
# input: time_assignments[time] is a map from spot index to (neuron index, euclidean distance to assigned cluster center) 
# output: neurons[n][time] = (location/profile of neuron n at time t, distance to cluster center)
def time_assignment_distances(time_assignments, num_neurons, full):
    neuron_times = [{} for _ in xrange(num_neurons)]
    for i in range(len(time_assignments)):
        frame = time_assignments[i]
        for j in range(len(frame)):
            # reverse a mapping from spot given by time_assignments[time][n] => (neuron, time)
            match = frame[j]
            neuron = match[0]
            neuron_time_map = neuron_times[neuron]            
            if i not in neuron_time_map or neuron_time_map[i][1] > match[1]:
                neuron_time_map[i] = [j, match[1]]
    # converts indices to coordinates
    for i in range(len(neuron_times)):
        neuron_times[i] = {k: (full[k][v[0]], v[1]) for k, v in neuron_times[i].items()}
    print 'paths found for %d neurons' % len(neuron_times)
    return neuron_times

# helper function for getting the average distance from each spot in neuron path to corresponding cluster center
# input: neuron track structure
# output: average distance of spots in the track to cluster center
def sum_distance(x):
    total = 0.0
    for time in x.keys():
        total += x[time][1]
    return total / len(x)

# helper function for getting the average displacement of neuron per frame 
# input: neuron track structure
# output: average neuron change distance of the track
# TODO: doesn't standardize differences in change occurances over different distances
def neuron_changes(neuron):
    count = 0.0
    tot = 0.0
    for t in range(len(neuron.keys())-1):
        count += 1
        time = neuron.keys()[t]
        nexttime = neuron.keys()[t + 1]
        tot += helpers.eucl(neuron[time][[0, 1]], neuron[nexttime][[0, 1]])
    return tot/count

# given a max average move threshold, remove neurons that jump around too much
# input: neuron tracks structure, jump distance structure
def traveler_removal(neurons, threshold):
    changes = list(map(neuron_changes, neurons))
    for i in sorted(range(len(changes)), reverse=True):
        if changes[i] > threshold:
            del neurons[i]