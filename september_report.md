# OVERVIEW

Goal was to improve the neuron tracking pipeline by constructing more neuron tracks (closer to the 600 in the ground truth) and improving correction methods. The main steps taken were changing the representation vectors from binary assignments (hard) to probabilistic assignments (soft), lowering the clustering distance to account for more clusters, and making heuristic improvements on the linear interpolation method used previously. 

Before the changes we got around 280 consistent (present in over half of the frames and free of jumps) tracks out of 450 total tracks. After the changes we get around 500 consistent tracks out of 550 total tracks. The change in clustering distance was the main contributing factor in the increased number of tracks, as the hard and soft representations yield similar numbers of total and consistent tracks. The hard clustering yields more tracks (both total and consistent), but the soft clustering yields longer tracks and requires less interpolation. 

# SOFT REGISTRATION

Previously each point was vectorized by concatenating the binary registration vectors obtained by one-hot encoding the point's projection to a set of registration vectors using CPD point set registration. CPD registration outputs a vector containing the probabilities of the desired point being mapped to each point in the reference frame. We previously set a assignment probability threshold: if there is a match with probability over the threshold the model point is mapped to the reference point in a one-hot registration vector, otherwise the model point is mapped to a zero vector. 

Because the registration vectors are simply clustered to obtain centers that represent neurons, we have freedom to choose any kind of representation to obtain the registration vectors. Probabilistic information is lost by using a hard representation; using the probability vectors themselves as the registration vectors provides a soft alternative to hard representation. Using soft registration vectors has the additional benefit of removing the assignment probability threshold, which is hard to tune due to its indirect effect on track quality. 

[This video](https://github.com/hydradarpa/hydra-neuron-tracking/blob/master/results/videos/overlay_tracks_september.mp4) displays all detected spots as diamonds and displays all tracks as circles to show how the tracks follow the neurons and account for gaps in detections. The tracks in the video are obtained with a clustering cutoff of 0.8, soft registration, and closest-point interpolation. 

![length_distribution_comparison](https://github.com/hydradarpa/hydra-neuron-tracking/blob/master/results/length_distribution_comparison.png "Length Distribution Comparison")

The graph above shows that the soft registration does not produce as many clusters holding the clustering distance constant, but more clusters may be obtained by lowering the clustering distance again for soft registration vectors. The blue bars represent consistent clusters, while the red ones represent inconsistent ones. As mentioned in the future steps, we will work on finding the tradeoff between getting more tracks and maintaining high track accuracy to tune this clustering distance more. 
![frame_assignment_comparison](https://github.com/hydradarpa/hydra-neuron-tracking/blob/master/results/track_count_comparison.png "Track Count Comparison")

The graph above shows the distributions of track lengths; tracks obtained from soft registration have a more bimodal distribution for length than those obtained from hard registration. The average consistent soft registration track had length 77, while the average consistent hard registration track had length 70. 

![frame_assignment_comparison](https://github.com/hydradarpa/hydra-neuron-tracking/blob/master/results/frame_assignments_comparison.png "Frame Assignment Comparison")

The graph above shows the number of spots assigned to a neuron at each frame (blue) compared to the total number of detections at each frame. For hard registration this spot count peaks at frame 50 before falling off, while the soft registration count stays high after rapidly rising around frame 50.

# CLOSEST POINT INTERPOLATION

Previously we interpolated gaps and jumps linearly; after detecting the start and end of a gap or jump we distribute the difference evenly over the intermediate time steps. While videos with less movement are locally linear, we want to be able to fill larger gaps and account for videos with rapid movement. 

The new interpolation method sequentially forms linear estimates: beginning with the start (the last known location), we predict the location at the next time step by dividing the distance between the end and the last known location by the number of time steps in between the two points. We identify the closest point to our estimate in the full set of spots at the given time step, and if the distance is below a constant threshold we use the closest point to fill in the gap/jump at that time step. We set the last known location as this interpolated point and repeat the process until the entire gap/jump is filled in. 
This method attempts to capture nonlinearities in a heuristic manner; rather than assuming a nonlinear model over the neuron movements, we correct for any differences between the actual neuron track and the linear prediction by filling in the gap with the closest actual detection to the estimate, rather than with the estimate itself. 

The next step for this interpolation method is computing the distance threshold as a function of the mean distance to closest point across all detections; undesirable performance can stem from a distance threshold that's too large, as detection errors may be compounded. It is also interesting to try applying this kind of interpolation only to jumps; gaps are more likely to suffer from these errors as they occur when there are no sufficiently close points in the first place. 

# FUTURE STEPS AND IDEAS

##### Segment Tracking And Track Splicing 

The current method employed cannot directly scale to large videos. As shown in the registration tuning report, the registration performs very poorly on frames that are over 50 time steps apart. This effect is also apparent in the assignment count graphs above; the tracking performs best near the middle of the video, where all reference frames are close enough to get closely correlated registration vectors and thus strong clusters. The assignment count graphs even reflect the asymmetry of the CPD accuracy, as the earlier frames (which are inaccurately mapped on to late frames) perform the worst. 

The other performance bottleneck comes from motion correction; the correction method links TPS transforms, which grows with the number of frames and becomes memory intensive for long videos. The registration and the motion correction bottleneck are both absent for 50 frame videos. 

The strategy going forward will be breaking a video into overlapping segments of 50 frames or less, tracking neurons in each segment, and then utilizing the overlap to stitch videos together. The number of reference frames for each registration stays constant, so the method scales well for large videos. The initial method for splicing tracks is to match each track in the first scene with the track in the second scene with the closest euclidean distance over the overlapped frames, then try more sophisticated transformations. 

##### Clustering Distance

One open issue is choosing the clustering distance that produces the optimal amount of tracks for a given video. The alternative approach to choosing a distance cutoff is specifying the number of clusters in advance. The main issue with the latter method is that we do not yet have good ways to predict the number of neurons from the video detections; not all neurons in a frame may be detected, and since neurons appear and disappear the true number of neurons at each frame may not be indicative of the total number of neurons either. For instance, in the ground truth data set there are 600 neurons, but only around 500 spots are detected at each frame. 

The current cutoff distance of 0.8 obtains a good amount of tracks (around 550 total, 500 consistent) on the test video for hard registration. The soft registration numbers are slightly lower. To optimize cutoff distance we can define an error metric in terms of consistent tracks and RMSE, then minimize it against all distance values. The main concern here is that we do not know if this approach can generalize to all videos without more ground truth training data; this generalization is an open problem.

##### Intensity Pattern Evaluation

An idea I had to address our lack of annotated data to evaluate our tracking methods on is to compare intensity patterns over each track to the intensity pattern across all neurons. We can get patterns of how the average neuron intensity evolves over time, and see if our tracks have "reasonable" intensity patterns relative to this average intensity pattern. Obviously the neurons don't all have the same activity patterns, but perhaps the average intensity pattern can be decomposed into the activity patterns of a couple of networks using signal processing methods and knowledge of the hydra nervous system. Alternatively, we can focus on the smoothness of intensity patterns for our tracks and simply check that any spikes coincide with spikes in the average intensity pattern. 

An intensity centered evaluation of neuron tracking would be a novel framework that can address the difficulty of obtaining ground truth data for neuron tracks. Using intensity makes sense for several reasons outside of the fact that it provides a self-contained method for evaluation. First off intensity measurements are fairly accurate in cell detection, especially in contrast with size measurements. Secondly we don't use intensity in our tracking or correction methods (the GMM registration uses intensity measurements but we're currently using the intensity-independent CPD registration), so smoothness in intensity serves as a sanity check for our tracks computed purely from position. Finally a big goal of neuron tracking is to analyze firing networks, so we should ensure that the networks deduced from our tracks match our biological understanding of hydra networks. 