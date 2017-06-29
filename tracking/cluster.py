import random
import numpy as np

from sklearn import metrics
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.cluster.hierarchy import fcluster

import helpers

# randomly choose fraction of registration vectors for clustering
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

# hierarchical agglomerative clustering with correlation distance
def correlation_hac(data, cutoff):
    links = linkage(data, 'complete', 'correlation')
    # process rounding errors
    for link in links:
        if link[2] < 0:
            link[2] = 0
    return fcluster(links, cutoff, criterion='distance')

# convert map from spots to cluster ID to a map from cluster ID to spots
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
            if True: # min(dists) < threshold:
                m = min(dists)
                assignments[n] = [dists.index(m), m]
                assigned += 1
        time_assignments.append(assignments)
    print '%d of %d spots were assigned to neurons' % (assigned, total)
    return time_assignments

# creates map from (neuron, time) to coordinates that represents the neuron's track
def process_assignments(time_assignments, num_neurons, full):
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
        neuron_times[i] = {k: full[k][v[0]] for k, v in neuron_times[i].items()}
    print 'paths found for %d neurons' % len(neuron_times)
    return neuron_times

