from pycpd import affine_registration
import gmmreg
import helpers
import numpy as np

# maps each spot in video to vector representation using gmm registration for vector construction
# input: full_spots[frame] is array of spots represented as (x, y, size, intensity)
# output: array of registration vectors (concatendated one-hot-encodings of registration mappings)
def gmm_registration(full, ref_indices):
    registrations = []
    matched = 0
    total = 0
    for frame in full:
        vec = [[] for _ in xrange(len(frame))]
        for i in ref_indices:
            ref = full[i]

            model = frame[:, [0, 1]]
            scene = ref[:, [0, 1]]
            m_info = [frame[:, 2], frame[:, 3]]
            s_info = [ref[:, 2], ref[:, 3]]
            model, scene, transformed = gmmreg.test_jt('/Users/jerrytang/summer2k17/hydra/data/hydra_config.ini', model, scene, m_info, s_info, False)

            matches = get_matches_dist(transformed, scene)
            # distance threshold
            threshold = np.mean(np.asarray(matches)[:,1])  
            for spot in range(len(matches)):
                total += 1
                match = matches[spot] # match is (assignment index, distance)
                reg = [0 for _ in xrange(len(ref))]
                if match[1] > threshold:
                    matched += 1
                    reg[match[0]] = 1
                vec[spot].extend(reg) # concatenate assignment vectors over all references
        registrations.append(vec)
    print 'each representation vector has length %d' % len(registrations[0][0])
    print 'got %d sufficiently close matches out of %d total' % (matched, total)
    return registrations

# maps each spot in video to vector representation using cpd registration for vector construction
# input: full_spots[frame] is array of spots represented as (x, y, size, intensity)
# output: array of registration vectors (concatendated one-hot-encodings of registration mappings)
def get_registration(full, ref_indices, threshold):
    registrations = []
    matched = 0
    total = 0
    for frame in full:
        vec = [[] for _ in xrange(len(frame))]
        for i in ref_indices:
            ref = full[i]
            mapping = affine_registration(Y=frame[:, 0:2], X=ref[:, 0:2])
            mapping.register(None)
            matches = get_matches_prob(mapping.Y, mapping.P)
            for spot in range(len(matches)):
                total += 1
                match = matches[spot] # match is (assignment index, distance)
                reg = [0 for _ in xrange(len(ref))]
                if match[1] > threshold:
                    matched += 1
                    reg[match[0]] = 1
                vec[spot].extend(reg) # concatenate assignment vectors over all references
        registrations.append(vec)
        print 'frame %d of %d registered' % (len(registrations), len(full))
    print 'each representation vector has length %d' % len(registrations[0][0])
    print 'got %d sufficiently close matches out of %d total' % (matched, total)
    return registrations

# assigns each frame spot to closest neuron in reference set based on euclidean distance
# input: array of frame spots, array of reference spots
# output: mappings[index of neuron in frame set] is (index of corresponding neuron in reference set, euclidean distance of transformed model spot to scene spot)
def get_matches_dist(frame, reference):
    mappings = []
    for spot in frame:
        dists = list(map(lambda x: helpers.eucl(x, spot), reference))
        match_index = dists.index(min(dists))
        match_dist = min(dists)
        mappings.append([match_index, match_dist])
    return mappings

# assigns each frame spot to closest neuron in reference set based on assignment likelihood
# input: array of frame spots, array of reference spots
# output: mappings[index of neuron in frame set] is (index of corresponding neuron in reference set, assignment likelihood of transformed model spot to scene spot)
def get_matches_prob(frame, probs):
    mappings = []
    for i in range(len(frame)):
        spot = frame[i]
        spot_probs = probs[i]
        match_prob = max(spot_probs)
        match_index = spot_probs.tolist().index(match_prob)
        mappings.append([match_index, match_prob])
    return mappings