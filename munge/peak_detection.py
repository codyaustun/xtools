import pandas as pd
from pandas import Series, DataFrame
import numpy as np
import matplotlib.pyplot as plt

class PeakDetector:

  def __init__(self, video_events):
    self.ve = video_events

  def trim_events(self, code, cutoff=20):
    video = self.ve[self.ve.code == code]
    duration = max(video.currentTime)
    video = video[(video.currentTime < duration - cutoff) & 
                  (video.currentTime > cutoff)]
    return video

  def peaks(self, video, num_bins=100, num_std=2, plot=True):
    
    # Take the video information and divide it into bins bins
    h,edges = np.histogram(video.currentTime, bins=num_bins)
    
    # Calculate the threshold
    t = h.mean() + num_std*h.std()
    
    # Create a series of value counts and edges
    time_counts = Series(h, index=edges[:-1])
    
    # Times the time_counts are above the threshold
    t_indices = time_counts[time_counts > t].index
    
    # Break all of the times above the threshold into neighborhoods
    neighborhoods = []
    in_hood = False
    for edge, count in time_counts.iteritems():
        if (in_hood) & (edge in t_indices):
            neighborhoods[-1] = neighborhoods[-1].set_value(edge, count)
        elif edge in t_indices:
            in_hood = True
            neighborhoods.append(Series())
            neighborhoods[-1] = neighborhoods[-1].set_value(edge, count)
        else:
            in_hood = False
    
    # Find the maximum point in each neighborhood
    peaks = Series()
    for neighborhood in neighborhoods:
        count = neighborhood.max()
        peak = neighborhood.idxmax()
        peaks = peaks.set_value(peak, count)
        
    # Plot the time counts, threshold line and peaks
    if plot:
        l = len(h)
        threshold_series = Series([t]*l)
        time_counts.plot()
        plt.plot(edges[:-1], threshold_series)
        peaks.plot(marker='o', color='r', ls='')
    
    return peaks