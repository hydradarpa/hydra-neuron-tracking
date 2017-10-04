import numpy as np
import helpers
import cluster
import evaluation
import registration
import processing
import correction
import constants

def splice(tracks, new_tracks, total_length, segment_length, overlap):
    success = 0.0
    for neuron_index in range(len(tracks)):
        neuron = tracks[neuron_index]
        match_index = -1
        # cutoff
        min_dist = 3.0
        min_num = 0
        stitching_base = total_length - overlap
        for match_try_index in range(len(new_tracks)):
            dist = 0.0
            num = 0.0
            match_try = new_tracks[match_try_index]
            for o in range(overlap):
                if stitching_base + o in neuron.keys() and o in match_try.keys():
                    dist += helpers.eucl(neuron[stitching_base + o][0:1], match_try[o][0:1])
                    num += 1
            if num > 0 and dist/num < min_dist:
                match_index = match_try_index
                min_dist = dist/num
                min_num = num
        if match_index != -1:
            success += 1
            for i in new_tracks[match_index].keys():
                if i + stitching_base in neuron.keys():
                    neuron[i + stitching_base] = (neuron[i + stitching_base] + new_tracks[match_index][i])/2.0
                else:
                    neuron[i + stitching_base] = new_tracks[match_index][i]
    print success
    print len(tracks)
    return total_length + segment_length - overlap

def get_tracks_hard(start, end, overlap_length, full, match_probability_threshold, cluster_cutoff_distance, cluster_accept_size, max_interpolation_length, correction_map=None, corrected_full=None):
    reference_indices = np.arange(0, end - start, overlap_length)
    registrations = registration.get_registration(full[start:end], reference_indices, match_probability_threshold)
    clustering_subset = cluster.get_subset(registrations, constants.CLUSTERING_SUBSET_FRACTION)
    cluster_assignments = cluster.correlation_hac(clustering_subset, cluster_cutoff_distance)
    clusters = cluster.reverse_map(cluster_assignments)
    centers = cluster.get_centers(clusters, clustering_subset, cluster_accept_size)
    time_assignments = cluster.assign_neurons(registrations, centers, constants.CENTER_ASSIGNMENT_DISTANCE)
    neurons = cluster.process_assignments(time_assignments, len(centers), full[start:end])
    
    if correction_map != None:
        neurons = processing.reverse_correction(neurons, correction_map[start:end])
        gap_corrected = correction.gap_interpolation(neurons, max_interpolation_length, corrected_full[start:end])
        jump_corrected = correction.jump_interpolation(gap_corrected, max_interpolation_length, corrected_full[start:end])
    
    consistent_tracks = correction.filter_consistent_tracks(jump_corrected, 5.0, 1)    
    return consistent_tracks

def get_tracks_soft(start, end, overlap_length, full, cluster_cutoff_distance, cluster_accept_size, max_interpolation_length, correction_map=None, corrected_full=None):
    reference_indices = np.arange(0, end - start, overlap_length)
    registrations = registration.get_soft_registration(full[start:end], reference_indices)
    clustering_subset = cluster.get_subset(registrations, constants.CLUSTERING_SUBSET_FRACTION)
    cluster_assignments = cluster.correlation_hac(clustering_subset, cluster_cutoff_distance)
    clusters = cluster.reverse_map(cluster_assignments)
    centers = cluster.get_centers(clusters, clustering_subset, cluster_accept_size)
    time_assignments = cluster.assign_neurons(registrations, centers, constants.CENTER_ASSIGNMENT_DISTANCE)
    neurons = cluster.process_assignments(time_assignments, len(centers), full[start:end])
    
    if correction_map != None:
        neurons = processing.reverse_correction(neurons, correction_map[start:end])
        gap_corrected = correction.gap_interpolation(neurons, max_interpolation_length, corrected_full[start:end])
        jump_corrected = correction.jump_interpolation(gap_corrected, max_interpolation_length, corrected_full[start:end])
    
    consistent_tracks = correction.filter_consistent_tracks(jump_corrected, 5.0, 1)    
    return consistent_tracks