import os
import subprocess
from skimage import io
import copy
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import glob
import cv2

# plots detected points in specified frame
# input: array of video frames, full spot structure, frame index, resolution, optional save path
def plot_frame(vid, full, frame, res, savepath=None):
    cp = copy.copy(vid[frame])
    for neuron in full[frame]:
        x = res * int(round(neuron[0]))
        y = res * int(round(neuron[1]))
        cv2.circle(cp, (x, y), 10, int(np.amax(cp)), 1)
    plt.imshow(cp, cmap="gray")
    if savepath:
        plt.savefig(savepath, dpi=800)
    
# returns copy of video with overlay for path of neuron n
# input: array of video frames, neuron id to track, neuron track structure, resolution 
def track_vid(vid, n, neurons, res):
    tracked = []
    for i in range(len(vid)):
        frame = vid[i]
        cp = copy.copy(frame)
        if i in neurons[n].keys():
            x = res * int(round(neurons[n][i][0]))
            y = res * int(round(neurons[n][i][1]))
            cv2.circle(cp, (x, y), 15, int(np.amax(cp)), 3)
        tracked.append(cp)
    return tracked

# returns copy of video with overlay for all neuron paths tracked by neuron index
# input: array of video frames, neuron track structure, resolution
def track_complete(vid, neurons, res):
    tracked = []
    for i in range(len(vid)):
        frame = vid[i]
        cp = copy.copy(frame)
        for n in range(len(neurons)):
            neuron = neurons[n]
            if i in neuron.keys():
                x = res * int(round(neuron[i][0]))
                y = res * int(round(neuron[i][1]))

                font = cv2.FONT_HERSHEY_SIMPLEX
                text = str(n)

                textsize = cv2.getTextSize(text, font, 1, 2)[0]
                textX = x - textsize[0] / 2
                textY = y + textsize[1] / 2
                cv2.putText(cp, text, (textX, textY ), font, 1, int(np.amax(cp)), 2)
        tracked.append(cp)
        print "%d tracked" %i
    return tracked

# returns copy of video with overlay for all neuron paths as open circles and all spots as points
# input: array of video frames, neuron track structure, resolution
def track_compare(vid, neurons, full, res):
    tracked = []
    for i in range(len(vid)):
        frame = vid[i]
        cp = copy.copy(frame)
        for n in range(len(neurons)):
            neuron = neurons[n]
            if i in neuron.keys():
                x = res * int(round(neuron[i][0]))
                y = res * int(round(neuron[i][1]))
                cv2.circle(cp, (x, y), 8, int(np.amax(cp)), 1)
        for spot in full[i]:
            x = res * int(round(spot[0]))
            y = res * int(round(spot[1]))
            cv2.circle(cp, (x, y), 2, int(np.amax(cp)), 3)
        tracked.append(cp)
        print "%d tracked" %i
    return tracked

# saves array of frames as video
# input: array of tracked video frames, save folder path
def save_vid(vid, folder):
    for i in xrange(len(vid)):
        plt.imshow(vid[i], cmap='gray')
        plt.savefig(folder + "/file%02d.png" % i, dpi=400)
    os.chdir(folder)
    subprocess.call([
        'ffmpeg', '-framerate', '8', '-i', 'file%02d.png', '-r', '30', '-pix_fmt', 'yuv420p',
        'tracked.mp4'
    ])
    for file_name in glob.glob("*.png"):
        os.remove(file_name)
    os.chdir('..')

# plot average neuron intensity across video
# input: full spots structure
def plot_avg_intensity(full):
    total_intensity = []
    for frame in full:
        tot = 0.0
        count = 0
        for spot in frame:
            count += 1
            tot += spot[4]
        total_intensity.append(tot/count)    
    plt.scatter(range(100), total_intensity)