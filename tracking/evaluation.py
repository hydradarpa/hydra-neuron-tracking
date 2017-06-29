import os
import subprocess
from skimage import io
import copy
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import glob
import cv2

# plots specified frame
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

# saves array of frames as video
def save_vid(vid, folder):
    for i in xrange(len(vid)):
        plt.imshow(vid[i], cmap='gray')
        plt.savefig(folder + "/file%02d.png" % i, dpi=1200)
    os.chdir(folder)
    subprocess.call([
        'ffmpeg', '-framerate', '8', '-i', 'file%02d.png', '-r', '30', '-pix_fmt', 'yuv420p',
        'tracked.mp4'
    ])
    for file_name in glob.glob("*.png"):
        os.remove(file_name)
    os.chdir('..')

def plot_luminance(vid):
    #centered = vid - np.min(vid)
    #stand = centered / float(np.max(centered))
    scaled = vid / float(np.max(scaled))

    lum = []
    for frame in scaled:
        c = 0
        for i in range(len(frame)):
            for j in range(len(frame[0])):
                c += frame[i][j]
        lum.append(c)
    rel = lum - np.min(lum)
    
    i = range(len(rel))
    plt.xlabel('time frame')
    plt.ylabel('relative intensity')
    plt.scatter(i, rel)

# average luminance per neuron
def plot_avg_luminance(vid):
    centered = vid - np.min(vid)
    stand = centered / float(np.max(centered))
    
    lum = []
    for frame in stand:
        c = 0
        for i in range(len(frame)):
            for j in range(len(frame[0])):
                c += frame[i][j]
        lum.append(c)
    rel = lum - np.min(lum)
    
    i = range(len(rel))
    plt.xlabel('time frame')
    plt.ylabel('relative intensity')
    plt.scatter(i, rel)

# neuron is neurons[i]
def plot_luminance_neuron(vid, neuron):
    vals = []
    for time in range(len(vid)):
        frame = vid[time]
        if time not in neuron:
            vals.append(0)
            continue
        x = int(neuron[time][0])
        y = int(neuron[time][1])
        vals.append(frame[x][y])
    vals = np.asarray(vals)
    plt.scatter(range(len(vals)), vals)
    plt.ylim(np.min(vals[np.nonzero(vals)]) - 50, np.max(vals[np.nonzero(vals)]) + 50)

def plot_count(full):
    counts = list(map(lambda x: len(x), full))
    plt.scatter(range(len(counts)), counts)