# REGISTRATION METHOD

Implementing and tuning the size and intensity sensitive Gaussian Mixture Model point set registration outlined in (http://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005517) which has applications in both motion correction and point set registration.

In the GMM registration method, each spot is represented as a Gaussian centered around spot center, with amplitude represented by the spot's intensity and standard deviation represented by the spot's size. Each frame is represented by a GMM by summing up the Gaussians representing each individual spot, and we fit a TPS on the model frame that minimizes the distance between the transformed model and the reference frame, given by the L2 norm of their GMM representations. 

Like the NRVE registration implementation, we introduce 2 multiplicative parameters, one for size and one for intensity in order to weigh the relative effects of distance, size, and intensity. Unlike the NRVE implementation, we hope to use a different size and intensity parameters for each registration depending on the inherent properties of the model and reference frames (eg change in average intensity). The tuning code is largely exploratory, so the next step is to create a predictive pipeline for inferring the optimal registration parameters from the frames that we're comparing. This approach would give us a fine-grained optimization for point set registration. 

To evaluate the accuracy of a temporal mapping, we load the ground truth data, which is stored in a neuron tracks structure. We use the consistent_coords function to map each detection in the model frame to the closest neurons in the ground truth data for the corresponding time. We repeat the process for the reference frame, ending up with ground-truth consistent frames for both the model and reference. We use the ground truth data to create a ground truth map between the time of the model frame and the time of the reference frame. We then perform the mapping from model to reference, and define the assignment accuracy as the percentage of model frame points that are correctly assigned.  

# MOTION CORRECTION

Motivation: correct for non-linearities before NRVE tracking using spatial continuity to move all videos to a constant frame of reference. The registration vector clustering approach is time-independent and loses information as a result; when projecting a spot to a registration vectors representing its global profile, the fact that its location at the next step should be close to its current location is lost. The motion correction hopes to encode this temporal information before the tracking method is performed. 

Technical details: we infer the motion of the hydra by mapping each spot in frame t to a spot in frame t + 1, picking fiducial points that are most likely to be correctly mapped. Using the fiducials as control points, we fit a TPS from the time t + 1 frame to the time t frame. Using these TPS transformations, we recursively map each frame back to space of the first frame. 

We initially used euclidean distance to map one frame to another by assigning each spot in frame t to the closest spot under euclidean distance in frame t + 1, but hypothesized that because the hydra moves rapidly, this mapping can be improved by taking size and intensity changes into account as well. We thus explored using Coherent Point Drift or the NRVE GMM registration as two point set registration improvements over the distance-only mapping. 

We make 2 choices that leave us with 6 possible registration strategy. First we choose a registration method: distance only, CPD, or GMM. Then we can either choose fiducials before or after the registration. If we choose fiducials from each frame first and then infer motion from mapping the fiducials, the registration is faster but less accurate, as the fiducials chosen in the time t frame may not correspond to any of the time t + 1 frame fiducials in the first place. Performing the point set registration first and then choosing the fiducials as the time t points that satisfy a given criteria, along with their assigned time t + 1 points, takes longer to run but performs better. The latter approach also provides the opportunity to draw the fiducials from assignments that we have high confidence in to be correct.  

Closest Distance:
* do not transform either frame
* assign each spot at time t to the closest one by euclidean distance at time t + 1
* baseline for other registrations due to simplicity and speed

CPD mapping: 
* a probabilistic model described here (https://papers.nips.cc/paper/2962-non-rigid-point-set-registration-coherent-point-drift.pdf)
* using Python implementation found here (https://github.com/siavashk/pycpd)
* no reliance on size or intensity, assigns purely on distance
* assignment of point s is given by probabilities of s being mapped to each point

GMM mapping:
* uses the method outline above
* runs over grid of size and intensity parameters to find optimal mapping
* mapping obtained from closest distance assignment between the transformed model frame and the reference frame

##### Parameters Used: 
* test_frames = [0, 20, 40, 60, 80]
* fiducial_percentage = 0.33
* size_params = [0, 0.25, 0.5, 0.75, 1.0]
* intensity_params = [0, 0.25, 0.5, 0.75, 1.0]

##### Results:
* Closest distance, fiducials first: 0.92381046449
* Closest distance, fiducials after: 0.97798031439
* CPD, fiducials first: 0.90917405246
* CPD, fiducials after: 0.97060580072 
* GMM, fiducials first: 0.89672357557
* GMM, fiducials after: 0.976476555

Across the board, we see that choosing fiducials before the registration performs worse than choosing fiducials after the registration. The main takeaway is that the naive closest distance mapping performs the best out of all of the methods. The GMM registration transforms the model frame by minimizing the GMM distance, but the mapping is still defined by using a closest distance assignment between the transformed frame and the reference frame. As the t to t + 1 frames line up very well already, transforming the points may introduce more registration errors without fixing the existing misassignments.

For faster moving videos the GMM registration may be more effective, as we later show that for larger gaps the fine-tuned GMM registration works very well. For the slow moving videos we're currently working with, we can improve the motion correction by choosing the right fiducials using the tracking methods employed here. Currently, fiducial points are chosen using a size and intensity threshold. Using the ground truth data and registration accuracy we can try to infer the properties of points that are registered property as a function of distance to other spots, size/intensity properties, and other metrics. We can then refine our fiducial selection process or come up with a general framework for selecting fiducials in hydra cell tracking.

# TRACKING

The GMM point set registration is also an integral part of the NRVE tracking pipeline. Currently I'm using coherent point drift for the registration step of the NRVE pipeline. Once again, we believe that the fine-tuned GMM can provide improves over CPD due to its optimality at each step; as described in the tracking report, the NRVE method performs a point set registration from every frame of the video to every reference frame. Because we're working with mappings across variable lengths of time and between frames with variable properties, it will be helpful to have a registration method that is tuned based off of the properties of the two frames it's matching. As before we want to infer size and intensity parameters from the metrics of the frames being matched, but we also want to consider the elapsed time between the frames. I hypothesize that for frames that are close in time distance will be the most important mapping factor, while intensity and size respectively dominate registrations over medium and long time frames. 

Once again, the analysis performed so far is mostly exploratory to see if size/intensity sensitive GMM registration is indeed an improvement over CPD methods, and whether it is feasible to predict size and intensity parameters from frame properties. We designate a set of reference frames and a set of model frames, and construct a map from an elapsed time e (reference time - model time) to a list containing the optimal accuracies (over all possible parameters) for mappings between all frames r and f such that r - f = e. We can then plot mean optimal accuracy as a function of elapsed time. 

##### Parameters:
* test_frames = [0, 20, 40, 60, 80]
* fiducial_percentage = 0.33
* size_params = [0, 0.25, 0.5, 0.75, 1.0]
* intensity_params = [0, 0.25, 0.5, 0.75, 1.0]
* full_indices = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]

##### Results:
As shown in the following graphs, both registration methods yield fairly symmetric results; CPD performs worse when elapsed time is positive and moderate/large, while GMM is actually better in these cases, suggesting that the method may be capitalizing on post spike intensity/size correlations. CPD performs very well for |elapsed time| > 25, staying above 80% accuracy. After that point, the method suffers a sharp fall to below 40% at |elapsed time| = 50 and before 20% around |elapsed time| = 75. On the other hand, GMM accuracy falls below 80% around |elapsed time| = 15, but then decreases linearly. In particular, the |elapsed time| = 50 and |elapsed time| = 75 values are respectively 0.5 and 0.3, an improvement over the CPD results. There are still ways to improve upon the GMM parameterization by factoring in expected intensity and size decreases, and there's the obvious question of how to tune the parameters now that we've established a correlation. 

![CPD](https://github.com/hydradarpa/hydra-neuron-tracking/blob/master/results/cpd_accuracies.png "CPD")

![GMM](https://github.com/hydradarpa/hydra-neuron-tracking/blob/master/results/gmm_accuracies.png "GMM")

# NEXT STEPS

##### Motion Correction:
* shift focus from tuning GMM to finding optimal fiducials under closest distance mapping
* tune fiducial percentage using Ben's trackings evaluation method

##### Tracking:
* introduce diminuishing effect; size and intensity multipliers inferred from global trends throughout the video in order to look for neurons a bit smaller (larger if elapsed time is negative) in intensity / size rather than the exact same. At the simplest this dimming factor can purely be a function of elapsed time, but we can also use frame properties since we know those beforehand; for instance a decrease in intensity between model frame f and reference frame f may be correlated to its dimming factor. If there is a need for fine tuning we can introduce a more sophisticated predictive method for dimming factor
* start building a predictive pipeline for size and intensity parameters