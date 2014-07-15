import sys
import datetime
import numpy as np
import scipy as sp
import pandas as pd
import datetime
import re
from pandas import Series, DataFrame

def age(year_of_birth):
    today = datetime.datetime.now()
    if (year_of_birth > 0) & (year_of_birth != ''):
        return today.year - int(year_of_birth)  #Should use today's year
    else:
        return np.NAN

def to_time(time):
    '''
    Takes a timestamp string from the tracking logs and turns it into a 
    np.datetime64 object

    Parameters
    ----------
    time : str
        Timestamp of a log event

    Returns
    -------
    time : np.datetime64
        Datetime object for the string timestamp

    '''
    # This is needed for some tracking log entries from MITx/8.02x/Spring_2013
    if isinstance(time, unicode) and time[-1] == 'd':
        time = time[:-1]
    return np.datetime64(time)

def total_time_spent(group):
    '''
    Calculates the total time spent from a group of person_object_time
    records
    
    Parameters
    ----------
    group : DataFrameGroupBy Object
        person_object_time records
        
    Returns
    -------
    total_time : float
        Seconds of total time spent
    '''
    data = group.time.order()
    durations = data.diff(-1)*-1
    max_time = np.timedelta64(30*60, 's')
    total_time = durations[durations < max_time].sum()
    return total_time / 10.**9