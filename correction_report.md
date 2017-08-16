# PURPOSE

Tracking errors can manifest in 2 ways:
1. The neuron path doesn't have a spot assigned at time t because the spot closest to the neuron was assigned to a different neuron or because there is no sufficiently close spot to the neuron at time t
2. The neuron path has a spot assigned at time t which is far away from the neuron's location at t - 1 due to clustering errors (the neuron's cluster center vector isn't really indicative of the neuron's profile)

To correct these errors, we performed two similar types of corrections; correcting for gaps, which are frames of no occurances sandwiched between 2 frames of occurances, as well as jumps, where the next occurance of a neuron is a significant distance away from all previous observations.

# GAP CORRECTION

Gap correction relies on spatial continuity to infer a neuron's position during a gap. Given 2 observances t and t + n, we interpolate the positions at t + 1, ..., t + n - 1 linearly from the endpoints at t and t + n. We are currently linearly interpolating size and intensity as well, but these are not robustly grounded like distance is; the neuron's path is locally linear, but changes in size and intensity are usually non-linear; a solution to this (and other problems) is proposed in the next steps. We define the maximum gap length that we can interpolate over as the max_interpolation_length parameter; for simplicity this interpolation length is the same for gaps and jumps.

We must also ensure that t and t + n positions are close; that is, there isn't a jump at t + n. Setting the jump threshold is still an open problem; since we're working with the tracks at this point we can get a heuristic for the average neuron displacement between frames t and t + n, but this value may be skewed by other jumps. 

# JUMP CORRECTION

Jumps are interpolated in the same way that gaps are, but jumps are detected via the observation that motion is usually in a single direction in the short run. A jump at time t + 1 occurs position(t) is closer to position(t + 2) than it is to position(t + 1). Currently we're defining a jump to be when the former distance is half the size as the latter distance (see tracking report for dicussion on tuning). When we're correcting we essentially discount time t + 1 as part of a gap with endpoints t and t + 2. 

An issue with jump correction is that jumps can represent either the correct track jumping to an error, or an error tracking jumping to the correct one. In the first case the jump correction removes the error, but in the second case the correction removes the good track in favor of the erroneous segment. Currently we are using the observation that an error must eventually go away (otherwise if spots from the error track perpetually show up the error track may as well be the real one), so eventually there will be a jump back to the correct track that will be too long to correct. The error is then cut out, as the consistent tracks ultimately returned are the contiguous segments of over 80 frames. I am looking into more sophisticated ways of doing this error correction, and this may result in more consistent tracks, as the discarding of error segments throws away track information. 

# NEXT STEPS

Many of the methods used here are heuristics, so now that we have a way of quantifying path accuracy several methods can be improved. In particular figuring out how to deal with discarded segments in jump correction may lead to many more neurons having consistent tracks

The immediate next step is to improve interpolation methods beyond the linear one currently employed. An obvious method is to estimate the position of the point using linear, then see if there are any detected points near the estimated position. If so, we can check whether the brightness and size follow the current trend of thr track. Using this approach we have a more robust method than simple linear interpolation, and we can also assign probabilities of each interpolated point being correct from several factors: distance to estimated point, intensity change, and size change. 