import copy
import time
import matplotlib.pyplot as plt
import gmmreg
import pandas as pd
import numpy as np

import helpers

# load files in the ICY ROI schema, consistent with motion correction pipeline
# input: array of csv path names
# output: full_spots[index] is array of all spots in frame at time index
def load_files(paths):
    vid = []
    for path in paths:
        vid.extend(load_file(path))
    print 'video loaded'
    return vid

# load individual csv file and return full_spots subarray, concatenated into full array
# input: csv path name of icy ROI detections
# output: full_spots[index] is array of all spots in frame at time index
def load_file(path):
    df = pd.read_csv(path)
    vid = []
    frame_count = int(np.nanmax(np.asarray(df['t']) + 1))
    for i in range(frame_count):
        frame = df[df.t == i]
        coords = frame[['x', 'y', 'Surface', 'max intensity']]
        tuples = [tuple(x) for x in coords.values]
        if len(tuples) != 0:
            vid.append(np.asarray(tuples))
    print 'loaded %d frames' % len(vid)
    return vid

# load ground truth tracks
# input: csv path name of ground truth tracks
# output: tracks[neuron] is a map from time to neuron profile at that time
def ground_truth_tracks(path):
    df = pd.read_csv(path)
    neuron_count = int(np.nanmax(np.asarray(df[df.columns[0]]) + 1))
    res = [{} for _ in xrange(neuron_count)]
    for i in range(neuron_count):
        mapping = df[df[df.columns[0]] == i]
        for row in mapping.itertuples():
            res[i][row[2] - 1] = (row[3]/2.0, row[4]/2.0)
    return res

# map detected data to ground truth data space by euclidean distance 
# input: full_spots structure, ground truth paths structure, frame index
# output: array of spots at given frame mapped to ground truth space
# TODO: arbitrary euclidean distance cut-off of 5 pixels in matching to closest point
def consistent_coords(detected_data, ground_truth, time):
    # construct list of ground truth positions at the given time
    time_list = []
    for neuron in ground_truth:
        if time in neuron.keys():
            time_list.append(neuron[time])

    # map each detected spot to closest ground truth position
    consistent = []
    for row in detected_data[time]:
        coords = (row[0], row[1])
        dists = list(map(lambda x: helpers.eucl(x, coords), time_list))
        match_index = dists.index(min(dists))
        match = time_list[match_index]
        if min(dists) < 5:
            cp = copy.copy(row)
            cp[0] = match[0]
            cp[1] = match[1]
            consistent.append(cp)
    return consistent

# convert ground truth data at a given time frame into map from current time to reference time
# input: ground truth tracks structure, current frame index, reference frame index
# output: mapping[spot] is profile of the spot in the reference frame
def ground_truth_map(ground_truth, current, reference):
    m = {}
    for neuron in ground_truth:
        if current in neuron.keys():
            m[neuron[current]] = neuron[reference]
    return m

# given a point set registration from between 2 frames return what percentage was mapped correctly
# input: registration map from current frame to reference frame, ground truth map from current frame to reference frame
# output: percentage of registration mappings that are correct under ground truth
def error(reg_map, ground_truth_map):
    count = len(reg_map.keys())
    right = 0.0
    for x in reg_map.keys():
        if reg_map[x] == ground_truth_map[x]:
            right += 1
    return right, count

# run size/intensity gmm registration
# input: frame index, reference index, [[size_param], [intensity_param]]
# output: array of model positions, array of reference positions, array of transformed positions; all under same indexing
def gmm_psr(frame, reference, param):
    m = frame[:, [0, 1]]
    s = reference[:, [0, 1]]
    m_info = [frame[:, 2], frame[:, 3]]
    s_info = [reference[:, 2], reference[:, 3]]
    model, scene, after = gmmreg.test('/Users/jerrytang/summer2k17/hydra/data/hydra_config.ini', m, s, m_info, s_info, False, param)
    return model, scene, after

# find max element and corresponding indices in matrix
# input: 2d array of accuracies
# output: (max accuracy, x index, y index)
def matrix_max(assignments):
    search = np.max(assignments)
    for i in range(len(assignments)):
        for j in range(len(assignments[0])):
            if assignments[i][j] == search:
                return (search, i, j)

# helper function for sorting by max intensity
def getKey(item):
    return item[3]

# get top x percent of fiducials by intensity
# input: array of detections for a frame, fraction of spots to take as fiducials
# output: array of fiducials
def get_fiducials_percentage(spots, percentage):
    total = int(percentage * len(spots))
    fid = sorted(spots, key=getKey, reverse=True)[0:total]
    return np.asarray(fid)

# get indices of top x percent of fiducials by intensity
# input: array of detections for a frame, fraction of spots to take as fiducials
# output: array of fiducial indices
def fid_percentage_index(spots, percentage):
    total = int(percentage * len(spots))
    fid = np.asarray(sorted(spots, key=getKey, reverse=True)[0:total])
    fid_int = list(map(lambda x: x[3], fid))
    cut = min(fid_int)
    indices = [index for index, spot in enumerate(spots) if spot[3] >= cut]
    return np.asarray(indices)

# get fiducials of a frame with a max intensity cutoff
# input: array of detections for a frame, intensity cutoff for spots to be classified as fiducials
# output: array of fiducials
def get_fiducials_cutoff(spots, cutoff):
    fid = []
    for spot in spots:
        if spot[3] > cutoff: 
            fid.append(spot)
    return np.asarray(fid)

# get sequential ground-truth-consistent registration sets for fiducials-first registration
# input: full spots structure, ground truth map, fiducial percentage, current frame
# output: array of current frame spots, array of reference frame spots
def get_registration_sets_fids(full, ground_truth, percentage, frame):  
    now_all = consistent_coords(full, ground_truth, frame)
    next_all = consistent_coords(full, ground_truth, frame + 1)
    now_fid = get_fiducials_percentage(now_all, percentage)
    next_fid = get_fiducials_percentage(next_all, percentage)    
    return now_fid, next_fid

# get sequential ground-truth-consistent registration sets for fiducials-after registration
# input: full spots structure, ground truth map, current frame
# output: array of current frame spots, array of reference frame spots
def get_registration_sets_full(full, ground_truth, frame):
    now_all = consistent_coords(full, ground_truth, frame)
    next_all = consistent_coords(full, ground_truth, frame + 1)
    now_all = np.asarray(list(map(lambda x: list(x), now_all)))
    next_all = np.asarray(list(map(lambda x: list(x), next_all)))
    return now_all, next_all

# match current frame coordinates to reference frame coordinates off of euclidean distance between transformed set and reference set
# input: list of current frame neurons, list of transformed current frame neurons, list of reference frame neurons, array of indices of fiducials in model set
# output: mapping[current frame neuron] is corresponding reference frame neuron
def get_distance_matches(model, transformed, reference, indices):
    mapping = {}
    # whole model set of fiducials-first registration, fiducial indices for fiducials-after registration
    for i in indices:
        dists = list(map(lambda x: helpers.eucl(x, transformed[i]), reference))
        match_index = dists.index(min(dists))
        match = reference[match_index]
        mapping[tuple(model[i])] = tuple(match)
    return mapping