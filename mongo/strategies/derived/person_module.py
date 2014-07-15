import sys
import datetime
import numpy as np
import scipy as sp
import pandas as pd
import re
from pandas import Series, DataFrame

from ..collection import CollectionStrategy
from ....munge import time as t

class PersonModuleStrategy(CollectionStrategy):

    @property
    def name(self):
        return 'derived_person_module'

    def create(self, context, max_time = 30*60, min_time = 0):
        '''
        Creates a DataFrame for the number of interactions and time spent by
        every user on each module in a course.

        Parameters
        ----------
        context : XData
            Provides methods for getting any data needed to create the 
            collection defined by this strategy as well as any additional 
            constraints

        max_time : int
            Upper limit for the number of seconds that can be spent on a module

        min_time : int
            Lower limit for the number of seconds that can be spent on a module

        Returns
        -------
        person_module : DataFrame

            Columns
            -------
            username : str
                edX username
            course_id : str
                edX course id. Ex: 'HarvardX/CB22x/2013_Spring'
            module_id : str
                Unqiue identifier for modules in a course
            time_spent : float
                Seconds the user spent on the module
            freq : int
                Number of times the user interacted with the module
        '''
        # Only want browser events, i.e. source = 1, since server events 
        #   don't indicate user time spent
        data = context.get('derived_person_object_time',
            conditions = {'source': 1},
            fields = ['time', 'username','module_id'])

        # The heavy lifting of this function was separated into 'from_data' in
        #   order to allow use of this processing on subsets of the
        #   person_object_time data 
        person_module = self.from_data(data)

        person_module['course_id'] = context.course_id
        return person_module

    def from_data(self, data, max_time = 30*60, min_time = 0):
        '''
        Creates a DataFrame for the number of interactions and time spent by
        every user on each module in a course.

        Parameters
        ----------
        data : DataFrame
            time, username, and module_id fields from derived_person_object_time

        max_time : int
            Max number of seconds for any duration

        min_time : int
            Min number of seconds for any duration

        Returns
        -------
        person_module : DataFrame

            Columns
            -------
            username : str
                edX username
            course_id : str
                edX course id. Ex: 'HarvardX/CB22x/2013_Spring'
            module_id : str
                Unqiue identifier for modules in a course
            time_spent : float
                Seconds the user spent on the module
            freq : int
                Number of times the user interacted with the module
        '''
        # Creates a series for the number of times that users interacted with
        #   the course modules which can easily be added to person_module later
        freq_data = data.loc[:,['username', 'module_id']]
        mod_freqs = freq_data.groupby(['username', 'module_id']).agg(len)

        # Due to inconsistencies in the logs pd.to_datetime didn't always work
        data['time'] = data['time'].apply(t.to_time)

        data = data.sort(['username','time']).reset_index()

        # Calling 'diff(-1)' on the time series creates a new series which is
        #   the time from the next event to the current one i.e. 
        #   current_time - next_time. Since the time stamps are in ascending
        #   order, this new series contains negative timedeltas, so the -1 makes
        #   the timedeltas positive
        data['time_spent'] = data.time.diff(-1)*-1

        # The time_spent in the last event for each user is invalid, because
        #   it is the time from the user's last event to the next user's first 
        #   event. To give a reasonable estimate of time these last events
        #   need to be removed.
        last_events = data.groupby('username').last()
        data = data[False == data['index'].isin(last_events['index'])]

        # Large gaps in time can appear in the logs when user goes away from the
        #   keyboard or logs off. To account for this, an upper limit can be set
        #   to remove such events.
        max_time = np.timedelta64(max_time, 's')
        limited = data[data['time_spent'] < max_time].loc[:,
            ['username','module_id', 'time_spent']]


        person_module = limited.groupby(['username', 'module_id']).agg(sum)
        person_module['freq'] = mod_freqs

        # Summing the timedeltas outputs nanoseconds which isn't human
        #   readable, so dividing by 10^9 turns this sum into seconds
        person_module['time_spent'] = person_module['time_spent'] / 10.**9
        person_module.reset_index(inplace = True) # removes multi-index

        return person_module
             
