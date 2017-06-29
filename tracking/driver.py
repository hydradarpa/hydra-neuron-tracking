import pickle
from skimage import io

import helpers
import cluster
import evaluation
import registration

# parameters

match_probility_threshold = 0.2
clustering_subset_fraction = 0.2
cluster_cutoff_distance = 0.9
cluster_accept_size = 0.001
center_assignment_distance = 1
ref_indices = [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240]

files = ['/Users/jerrytang/summer2k17/hydra/data/contract_512_7_1.csv', '/Users/jerrytang/summer2k17/hydra/data/contract_512_7_2.csv', '/Users/jerrytang/summer2k17/hydra/data/contract_512_7_3.csv']
video_path = '/Users/jerrytang/summer2k17/hydra/data/contract.tif'
# res is 2 for 512 images, 1 for 1024
res = 2 
neuron_to_track = 8
video_save_folder = '/Users/jerrytang/summer2k17/hydra/temp_video'
assignments_save_path = '/Users/jerrytang/summer2k17/hydra/neuron_assignments_real_2.csv'

full = helpers.load_files(files)

# registration[time][spot] = {vector representation of that spot}
registration = registration.gmm_registration(full, [0, 40, 80, 120, 160, 200, 240])

# flat array of nonzero spot vectors
clustering_subset = cluster.get_subset(registration, clustering_subset_fraction)

# cluster_assignments[index] is the cluster that the vector at clustering_subset[index] is assigned to
cluster_assignments = cluster.correlation_hac(clustering_subset, cluster_cutoff_distance)

# clusters[i] = list of indices in clustering_subset for vectors assigned to cluster i
clusters = cluster.reverse_map(cluster_assignments)

# centers[i] = vector representing the center for the cluster of neuron i
centers = cluster.get_centers(clusters, clustering_subset, cluster_accept_size)

# time_assignments[time] = map from spot index to (neuron index, distance)
time_assignments = cluster.assign_neurons(registration, centers, center_assignment_distance)

# neurons[n][time] = location of neuron n at time t
neurons = cluster.process_assignments(time_assignments, len(centers), full)

helpers.write_neuron_assignments(neurons, assignments_save_path)

vid = io.imread(video_path)

tracked = evaluation.track_vid(vid, neuron_to_track, neurons, res)

evaluation.save_vid(tracked, video_save_folder)

