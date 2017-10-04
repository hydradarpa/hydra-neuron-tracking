import random
import numpy as np

from sklearn import metrics
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.cluster.hierarchy import fcluster

import helpers

# randomly choose fraction of registration vectors for clustering
# input: array of registration vectors, fraction of registration vectors to sample
# output: array of sampled registration vectors
def get_subset(registration, frac):
    count = 0
    subset = []
    for frame in registration:
        count += len(frame)
        if random.random() > frac:
            continue
        for vec in frame:
            if np.count_nonzero(vec) != 0:
                subset.append(vec)
                count += 1
    print 'sampled %d of %d registration vectors for clustering' %(len(subset), count)
    return subset

# hierarchical agglomerative clustering with correlation distance metric
# input: array of sampled registration vectors, HAC distance cutoff
# output: cluster_assignments[registration vector] is the cluster ID that the vector is assigned to
def correlation_hac(data, cutoff):
    links = linkage(data, 'complete', 'correlation')
    # process rounding errors
    for link in links:
        if link[2] < 0:
            link[2] = 0
    return fcluster(links, cutoff, criterion='distance')

# convert map from spots to cluster ID to a map from cluster ID to spots
# input: cluster_assignments[registration vector] is the cluster ID that the vector is assigned to
# output: clusters[i] is the set of registration vectors assigned to cluster i
def reverse_map(clusters):
    reverse = {}
    for i in range(len(clusters)):
        val = clusters[i]
        if val not in reverse:
            reverse[val] = []
        reverse[val].append(i)
    print 'total of %d nonempty clusters' %len(reverse)
    return reverse

# returns centers (corresponding to neurons) of clusters containing large enough % of clustering subset
# input: clusters[i] is the set of registration vectors assigned to cluster i, set of registration vectors used for clustering, percent of vectors that a valid cluster needs to contain
# output: array of cluster centers
def get_centers(clusters, subset, threshold):
    centers = []
    for cluster in clusters.values():
        if len(cluster) > threshold * len(subset):
            center = np.zeros(len(subset[0]))
            for j in cluster:
                center += np.asarray(subset[j])
            centers.append(np.divide(center, float(len(cluster))))
    print '%d of %d clusters qualified as neurons' % (len(centers), len(clusters))
    return centers

# assigns each (time, spot) to the closest neuron under a distance threshold
# input: array of registration vectors, array of cluster centers, distance threshold for registration vector to be assigned to a neuron (cluster center)
# output: time_assignments[time] is a map from spot index to (neuron index, euclidean distance to assigned cluster center) 
def assign_neurons(registrations, centers, threshold):
    time_assignments = []
    total = 0
    assigned = 0
    for frame in registrations:
        assignments = {}
        for n in range(len(frame)):
            # get vector representation of spot n of frame
            vec = frame[n]
            dists = list(map(lambda x: helpers.eucl(x, vec), centers))
            total += 1
            if min(dists) < threshold:
                m = min(dists)
                assignments[n] = [dists.index(m), m]
                assigned += 1
        time_assignments.append(assignments)
        print 'frame %d of %d registered' % (len(time_assignments), len(registrations))
    print '%d of %d spots were assigned to neurons' % (assigned, total)
    return time_assignments

# processes time assignments to construct neuron tracks
# input: time_assignments[time] is a map from spot index to (neuron index, euclidean distance to assigned cluster center) 
# output: neurons[n][time] = location/profile of neuron n at time t
def process_assignments(time_assignments, num_neurons, full):
    neuron_times = [{} for _ in xrange(num_neurons)]
    for i in range(len(time_assignments)):
        frame = time_assignments[i]
        for j in frame.keys():
            # reverse a mapping from spot given by time_assignments[time][n] => (neuron, time)
            match = frame[j]
            neuron = match[0]
            neuron_time_map = neuron_times[neuron]            
            if i not in neuron_time_map or neuron_time_map[i][1] > match[1]:
                neuron_time_map[i] = [j, match[1]]
    # converts indices to coordinates
    for i in range(len(neuron_times)):
        neuron_times[i] = {k: full[k][v[0]] for k, v in neuron_times[i].items()}
    print 'paths found for %d neurons' % len(neuron_times)
    return neuron_times