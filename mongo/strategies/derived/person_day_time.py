import sys
import datetime
import math
import numpy as np
import scipy as sp
import pandas as pd
from pandas import Series, DataFrame

from ..collection import CollectionStrategy
from ....munge import time as t

class PersonDayTimeStrategy(CollectionStrategy):
    
    @property
    def name(self):
        return 'derived_person_day_time'
    
    def create(self, context, max_time = 30*60, min_time = 0):
        '''
        Creates a DataFrame of daily time spent by users in a course

        Parameters
        ----------
        context : XData
            Provides methods for getting any data needed to create the 
            collection defined by this strategy as well as any additional 
            constraints

        Returns
        -------
        data : DataFrame

            Columms
            -------
            username : str
                edX username
            date : str
                Calendar date in the format '%Y-%m-%d'. Ex: '2013-02-11'
            time_spent : float
                Seconds of total time spent
        '''
        # Only want browser events, i.e. source = 1, since server events 
        #   don't indicate user time spent
        pot = context.get('derived_person_object_time',
            conditions = {'source': 1},
            fields = ['time', 'username'])
        
        person_day_time = self.from_data(pot)

        person_day_time['course_id'] = context.course_id

        return person_day_time

    def from_data(self, data):
        '''
        Creates a DataFrame of daily time spent by users in a course

        Parameters
        ----------
        data : DataFrame
            time and username fields from derived_person_object_time

        Returns
        -------
        data : DataFrame

            Columms
            -------
            username : str
                edX username
            date : str
                Calendar date in the format '%Y-%m-%d'. Ex: '2013-02-11'
            time_spent : float
                Seconds of total time spent
        '''
        # The time field in person_object_time is a str, so we can quickly slice
        #   off the date. This is much faster than converting all times to
        #   datetime object
        data['date'] = data['time'].apply(lambda x: x[:10])
        data['time'] = data.time.apply(t.to_time)

        grouped = data.groupby(['username','date'])
        person_day_time = grouped.apply(t.total_time_spent)
        person_day_time.name = 'time_spent'
        person_day_time = person_day_time.reset_index()
        return person_day_time