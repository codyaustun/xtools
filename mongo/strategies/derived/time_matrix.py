import sys
import datetime
import numpy as np
import scipy as sp
import pandas as pd
import re
from pandas import Series, DataFrame


from ..collection import CollectionStrategy
from ....munge import time as t

class TimeMatrixStrategy(CollectionStrategy):

    @property
    def name(self):
        return 'derived_time_matrix'

    def create(self, context, max_time = 30*60, min_time = 0):
        '''
        Create a matrix of time for every module_id in a course
        and every user

        Parameters
        ----------
        context : XData
            Provides methods for getting any data needed to create the 
            collection defined by this strategy as well as any additional 
            constraints

        max_time : int
            Max number of seconds for any duration

        min_time : int
            Min number of seconds for any duration

        Returns
        -------
        data : DataFrame

            Columns
            -------
            username : str
                edX username
            module_id* : float
                seconds of time spent on the module_id
        '''
        data = context.get('derived_person_object_time',
            conditions = {'source': 1},
            fields = ['time', 'username','module_id'])

        time_matrix = self.from_data(\
            data,
            max_time = max_time,
            min_time = min_time).reset_index()

        time_matrix['course_id'] = context.course_id

        return time_matrix

    def from_data(self, data, max_time = 30*60, min_time = 0):
        '''
        Create a matrix of time for every module_id in a course
        and every user

        Parameters
        ----------
        data : DataFrame
            time, username, module_id fields from derived_person_object_time

        max_time : int
            Max number of seconds for any duration

        min_time : int
            Min number of seconds for any duration

        Returns
        -------
        data : DataFrame

            Columns
            -------
            username : str
                edX username
            module_id* : float
                seconds of time spent on the module_id
        '''

        # Convert to Datetime
        data['time'] = data['time'].apply(t.to_time)

        # Sort & Diff
        data = data.sort(['username','time']).reset_index()
        data['duration'] = data.time.diff(-1)*-1

        # Remove Last Events
        last_events = data.groupby('username').last()
        data = data[False == data['index'].isin(last_events['index'])]

        max_time = np.timedelta64(max_time, 's')
        min_time = np.timedelta64(min_time, 's')
        limited = data[data['duration'] < max_time].loc[:,
            ['username','module_id', 'duration']]
        # limited = data.loc[:,['username','module_id', 'duration']]
        # limited.ix[limited.duration > max_time, 'duration'] = max_time
        # limited.ix[limited.duration < min_time, 'duration'] = min_time

        if not limited.empty:
            time_matrix = limited.pivot_table(rows = 'username',
                cols = 'module_id',
                values = 'duration',
                aggfunc = sum).fillna(0)

            # Turn nanoseconds to seconds
            time_matrix = time_matrix / 10.**9
            return time_matrix
        else:
            return DataFrame()