# TERMINOLOGY

Time: times are represented by frame indices
Spot: detected point in a frame represented as (x, y, size, intensity) tuple
Neuron: neuron profile represented as a center of a registration vector cluster
Track: a map from time to a neuron's position at that time

# PROCESS

Input: full spots structure representing the spots at each frame, where full_spots[frame_index] is a list of spots 
Output: track structure representing the tracks for each neuron, where tracks[neuron_index] is a map from time to corresponding spot

The tracking pipeline consists of 4 steps: registration, clustering, assignment, and correction. The first 3 steps follow the NRVE method outlined here (http://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005517), and I will describe my implementation details and design decisions in applying the method to the hydra tracking problem. The correction step is a set of heuristic methods I added that take advantage of spatial continuity to reduce potential errors in the tracks. 

##### 0. Motion Correction:

See motion correction section in the tuning doc. We are currently using an ICY plugin implementing the closest distance motion correction. The motion correction step is performed in ICY following the ICY detections; the motion corrected spots are saved as a CSV file, along with a motion correction CSV file that maps each spot's motion corrected coordinates to its original coordinates. 

The rest of the code is currently in written in the Python files [helpers.py](https://github.com/hydradarpa/hydra-neuron-tracking/blob/master/tracking/helpers.py), [registration.py](https://github.com/hydradarpa/hydra-neuron-tracking/blob/master/tracking/registration.py), [cluster.py](https://github.com/hydradarpa/hydra-neuron-tracking/blob/master/tracking/cluster.py), [processing.py](https://github.com/hydradarpa/hydra-neuron-tracking/blob/master/tracking/processing.py), [correction.py](https://github.com/hydradarpa/hydra-neuron-tracking/blob/master/tracking/correction.py), and [evaluation.py](https://github.com/hydradarpa/hydra-neuron-tracking/blob/master/tracking/evaluation.py). These files align with the steps of the tracking pipeline.

##### 1. Registration: 
Given a reference frame r, a spot in model frame f can be represented by the one-hot-encoded vector storing the index of the corresponding spot in frame r under a point set registration between frames f and r. By concatenating the representation vectors of a spot over a set of reference frames, a global profile is constructed for each spot in each frame. We can then define a neuron as a set of spots across time that share similar profiles. 

Steps:
1. helpers.load_files: reads the full_spots structure from motion corrected ICY detections CSV file
2. helpers.get_registration: constructs a list of representation vectors from the full_spots structure, the reference_indices parameter, and the match_probability_threshold parameter

Design Decisions:
* reference_indices: currently choosing every 10th frame as a reference frame but for larger videos it may be useful to use frames with high average spot intensity (signifying spikes) as reference frames
* registration method: currently using the probabilistic Coherent Point Drift method which relies purely on spatial coordinates for registration. Working on tuning the size/intensity sensitive GMM method as an alternative to CPD (see tuning documentation) 
* match_probility_threshold/match_distance_threshold: used as the match cutoff for CPD and GMM registrations, respectively. After the point set registration method transforms the model frame, the points in the transformed frame must be matched to the reference frame points. Raising the probability threshold or lowering the distance threshold increases the number of spots that aren't assigned to any corresponding spots (a registration vector of all zeros). Tuning these thresholds is an open problem that should improve perfomance; visualizing the change in accuracy against ground truth tracks for different threshold values is a good place to start 

##### 2. Clustering: 

From the flat array of representation vectors, we can construct clusters of similar vectors. The centers of the clusters represent the time-invariant neuron profiles. Spots can be then assigned to neurons by going through each frame and assigning each spot to the neuron with the closest representation vector.

Steps:
1. cluster.get_subset: samples clustering_subset_fraction of the registration vector array for clustering
2. helpers.correlation_hac: performs hierarchical agglomerative clustering on the sampled registration vector array, using correlation distance as the clustering metric and cluster_cutoff_distance as the cutoff distance. Outputs a map from representation vector to cluster ID
3. helpers.reverse_map: takes the map from representation vectors to cluster ID and returns a map from cluster ID to an array of representation vectors assigned to that cluster
4. helper.get_centers: returns a list of the centers of the clusters that are a high enough percentage (thresholded by cluster_accept_size) of the clustering subset

Design Decisions:
* clustering_subset_fraction: coarse tuned to reduce clustering times while ensuring that enough vectors are sampled to create accurate neuron profiles
* clustering method: HAC can be tuned by decreasing cluster_cutoff_distance (to get more neurons), currently using the default of 0.9 used in the NRVE method. If a good heuristic is found to estimate the total number of neurons from the number of detected spots at each frame, kmeans clustering could be a viable alternative that ensures a given number of clusters
* cluster_accept_size: raising this cutoff decreases the number of clusters accepted as neurons. Currently set very low, with the assumption that the correction step is a more intuitive method of correcting erroneous assignments than tuning this parameter. An issue is that when a spot is assigned a "fake neuron" (one that would be rejected under a higher cluster accept cutoff), the information about the spot's real assignment is lost. Tuning this parameter is thus still an open problem. 

##### 3. Assignment:  
Given the neurons represented by cluster centers, we construct tracks by assigning each spot at each frame to its closest neuron.

Steps:
* cluster.assign_neurons: maps spots to their closest neurons by euclidean distance of registration vectors using a center_assignment_distance threshold
* cluster.process_assignments: takes the time_assignments map obtained in the previous set and outputs it in the desired neuron_tracks structure. This function also ensures that no neuron is assigned to multiple spots; if multiple spots in a frame are matched with a neuron, the closest pair in euclidean distance ends up as the correct assignment

Design Decisions:
* center_assignment_distance: like for the cluster_accept_size, this distance cutoff is set arbitrarily large, as the correction step can correct for missing and incorrect neuron assignments in a clearer way than this threshold

##### 4. Correction:

Before correction, the tracks often have jumps or gaps from errors in assignment. The correction step fills in gaps and corrects jumps - there are paths that are inconsistent (with large jumps) even after correction, so these paths are filtered out. The correction step also provides a more intuitive alternative than parameter tuning for tracking; rather than being strict on cluster assignments, we can be relax cutoff parameters and defer all errors to the correction step. Detailed description of the gap and jump interpolations can be found in the correction doc. 

Steps:
* correction.gap_interpolation: fills in gaps in a neuron path where the neuron does not have a corresponding spot
* correction.jump_interpolation: fills in jumps in a neuron path where spatial continuity is broken
* correction.filter_consistent_tracks: removes tracks that have large jumps even after gap and jump correction, returning a set of consistent tracks

Design Decisions:
* max_interpolation_length: increasing this parameter causes more paths to be considered consistent, as larger gaps and jumps are removed, but the interpolation accuracy decreases, especially for the linear interpolation method that is currently used. In the process of tuning this parameter
* jump correction heuristic: currently a jump is defined at time t + 1 when the distance between position(t) and position(t + 2) is less than x times the distance between position(t) and position(t + 1). x is currently set at 0.5; increasing the parameter classifies more times as jumps, still in the process of tuning this heuristic
* track consistency jump heuristic: after gap and jump correction, the correction.filter_consistent_tracks function removes tracks that still contain a jump of over y pixels, where y is currently set at 3. Currently working on ways to tune this heuristic using ground truth track statistics

# RESULTS

##### Parameters:
* reference_indices = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
* match_probability_threshold = 0.2
* clustering_subset_fraction = 0.2
* cluster_cutoff_distance = 0.9
* cluster_accept_size = 0.001
* center_assignment_distance = 1
* max_interpolation_length = 10
* frame_occurence_threshold = 50

##### Results:
* Total tracks: 450
* Consistent tracks: 280

##### Statistics:
* RMSE: 6.08
* Median proportion of track within 6 pixels: 0.54
* Percentage of consistent tracks that are all within 6 pixels: 12.9

A video showing the results is found [here](https://github.com/hydradarpa/hydra-neuron-tracking/blob/master/results/videos/gaplength_10_length_50.mp4). The blue points show ground truth tracks that were matched with estimated tracks. The green/red points show estimated tracks that are within/not withing 6 pixels of the truth.

# NEXT STEPS

##### 1. Construct tracks for more neurons:
Current approach / set of parameters is getting only 450 total tracks from which 280 consistent tracks are obtained, while the ground truth data contains 600 total tracks.

Potential Solutions:
* change clustering methods to create more clusters (relax distance cutoff, try k-means)
* improve point set registration by size/intensity tuning, as improved accuracy of registration vectors leads to more consistent clusters, eliminating the clusters that are too small to be considered neurons

##### 2. Get more consistent tracks:
280 of the 450 NRVE tracks are marked as consistent after my correction methods are applied, so raising the probability of detected tracks that are consistent is very important.

Potential Solutions:
* modify interpolation methods and look into ways to recycle discarded jump segments, more details in correction doc
Potential Solutions:
* dealing with "discarded" spots: jumps are removed by correction.jump_interpolation, but often the jumps are segments of a different track that end up getting discarded. Looking into methods for stiching up jump segments to reconstruct tracks that are currently discarded
* currently using a linear interpolation method, but size and intensity continuity can be utilized as well in filling in gaps and jumps. Furthermore the interpolated neurons can be mapped to detected neurons in the frame, and interpolated segments can be assigned probabilities based on how close the interpolated points are to the real detections