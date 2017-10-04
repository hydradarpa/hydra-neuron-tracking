import helpers
import copy

# linearly interpolate points between start and end
# input: neuron track structure, start spot, end spot
def interpolate(track, start, end, full=None):
    diff = track[end] - track[start]
    length = end - start
    for i in range(1, length):
        estimate = track[start] + i * diff / length   
        if full==None:
            track[start + i] = estimate
            return False     
        dists = list(map(lambda x: helpers.eucl(x, estimate[[0, 1]]), full[start + i][:, [0, 1]]))
        match_index = dists.index(min(dists))
        match_dist = min(dists)
        if match_dist < 3.0:
            track[start + i] = full[start + i][match_index]
            return True
        else:
            track[start + i] = estimate
            return False

# interpolate gaps in neuron path between consistent points up to a gap length threshold
# input: neuron tracks structure, max length of gap that can be interpolated over
# output: neuron tracks structure with interpolated points
def gap_interpolation(neurons, tolerance, full):
    corrected_map = copy.deepcopy(neurons)
    real_detection_matched = 0
    tot = 0
    for neuron in corrected_map:
        if len(neuron.keys()) == 0:
            continue
        for n in range(max(neuron.keys())):
            if n in neuron.keys() and n + 1 not in neuron.keys():
                last = neuron[n]
                for i in range(tolerance):
                    if n + i in neuron.keys():
                        test = neuron[n + i]
                        if helpers.eucl(last[[0, 1]], test[[0, 1]]) < 2.0:
                            matched = interpolate(neuron, n, n + i, full)
                            tot += 1
                            if matched:
                                real_detection_matched += 1
    print real_detection_matched
    print tot
    return corrected_map

# interpolate jumps in neuron path between consistent points up to a gap length threshold
# input: neuron tracks structure, max length of gap that can be interpolated over
# output: neuron tracks structure with interpolated points
def jump_interpolation(neurons, tolerance, full):
    corrected_map = copy.deepcopy(neurons)
    real_detection_matched = 0
    tot = 0
    for neuron in corrected_map:
        for n in neuron.keys():
            candidates = sorted([s for s in neuron.keys() if s > n and s - n - 1 <= tolerance])
            if len(candidates) < 2:
                continue
            jump = candidates[0]
            falls = candidates[1:]
            for fall in falls:
                if helpers.eucl(neuron[n][[0, 1]], neuron[jump][[0, 1]]) > 2 * helpers.eucl(neuron[n][[0, 1]], neuron[fall][[0, 1]]):
                    matched = interpolate(neuron, n, fall, full)        
                    tot += 1
                    if matched:
                        real_detection_matched += 1                
                    break;
    print real_detection_matched
    print tot
    return corrected_map

# get indices where the neuron track jumps over a given distance threshold
# input: neuron tracks structure
# output: indices of jumps in neuron track
# TODO: using arbitrary euclidean distance of 3 pixels to identify jumps
def get_jump_indices(neuron, threshold):
    tot = []
    for i in range(len(neuron.keys())-1):
        ind = neuron.keys()[i]
        indplus = neuron.keys()[i + 1]

        cur = neuron[ind]
        nex = neuron[indplus]
        #print helpers.eucl([cur[0], cur[1]], [nex[0], nex[1]])
        tot.append(helpers.eucl([cur[0], cur[1]], [nex[0], nex[1]]))
    a = [index for index, jump in enumerate(tot, 1) if jump > threshold]
    return a

# return consistent tracks that don't contain any jumps
# input: neuron tracks structure
# output: consistent neuron tracks structure
# TODO: change start and end cutoffs of 20 and 80
def filter_consistent_tracks(tracks, threshold, max_jumps):
    combined = []
    for neuron in tracks:
        if len(get_jump_indices(neuron, threshold)) <= max_jumps:
            combined.append(neuron)
        elif max(get_jump_indices(neuron, threshold)) < 20:
            dup = copy.deepcopy(neuron)
            for i in dup.keys():
                if i < 20:
                    del dup[i]
            combined.append(dup)
        elif min(get_jump_indices(neuron, threshold)) > 80:
            dup = copy.deepcopy(neuron)
            for i in dup.keys():
                if i > 80:
                    del dup[i]
            combined.append(dup)
    return combined