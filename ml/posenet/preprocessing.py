import cv2
import time
import argparse
import torch
from sklearn import preprocessing
import numpy as np
# import posenet
import numpy as np
from scipy.spatial.distance import cosine
from fastdtw import fastdtw
import re
import numpy as np


PART_NAMES = [
    "leftShoulder", "rightShoulder", "leftElbow", "rightElbow", "leftWrist", "rightWrist",
    "leftHip", "rightHip", "leftKnee", "rightKnee", "leftAnkle", "rightAnkle"
]

def Normalize(pose_scores, keypoint_scores, keypoint_coords, thresh=0.1):
    keypoint_scores = keypoint_scores.reshape((17, -1))
    keypoint_coords = keypoint_coords.reshape((17, 2))

    # Step 1: filter out bad scores
    mask = (keypoint_scores.ravel() > thresh)
    if not np.any(mask):
        return {}

    # Step 2: Crop
    min_x = np.min(keypoint_coords[mask, 0])
    min_y = np.min(keypoint_coords[mask, 1])
    keypoint_coords[:, 0] -= min_x
    keypoint_coords[:, 1] -= min_y

    # Step 3: Normalize
    normalized_coords = preprocessing.normalize(keypoint_coords, norm='l2')

    # Step 4: Convert to dict
    output = {}
    for i in range(17):
        if mask[i]:
            output[posenet.PART_NAMES[i]] = (normalized_coords[i, 0], normalized_coords[i, 1])
    return output

def TimeSeries(dictionaries):
    # combines list of dictionaries
    TimeSeries = {}
    # Iterate every part name and combine part values
    for k in PART_NAMES:
        tups = [TimeSeries[k] for TimeSeries in dictionaries if k in TimeSeries]
        TimeSeries[k] = ()
        for t in tups:
            TimeSeries[k] += t
    return TimeSeries

def DTW(dict1,dict2):
    # computes the DTW between two dictionaries & values
    # outputs distances to dictionary distances
    distances = {}
    for key in dict1:
        if key in PART_NAMES:
            if dict1[key] and dict2[key]:
                x = np.array(dict1[key]) + 0.00001
                y = np.array(dict2[key]) + 0.00001
                distances[key] = fastdtw(x, y, dist=cosine)[0]
    return distances


def MovePart(distances):
    # Prints and outputs which body part to use
    # Calculated by body part with the highest distance in DTW
    movePart = max(distances, key=distances.get)
    res_list = re.sub("([a-z])([A-Z])","\g<1> \g<2>", movePart)
    movePart = ''.join(res_list).lower()
    print('Move your %s.' %movePart)
    return movePart