import sys
import datetime
import math
import numpy as np
import scipy as sp
import pandas as pd
from pandas import Series, DataFrame

from ..collection import CollectionStrategy

class PersonDayEventsStrategy(CollectionStrategy):

    @property
    def name(self):
        return 'derived_person_day_events'

    def create(self, context):
        '''
        Creates a DataFrame of daily events counts for users in a course

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
            course_id : str
                edX course id. Ex: 'HarvardX/CB22x/2013_Spring'
            verb* : int
                Additional columns representing the count of specific event
                types for a user on a specific date. These columns vary with
                between courses as course may only generate a subset of the
                possible events
        '''
        pot = context.get('derived_person_object_time',
            fields = ['username','verb','time'])

        # The time field in person_object_time is a str, so we can quickly 
        #   slice off the date. This is much faster than converting all times 
        #   to datetime object
        pot['date'] = pot['time'].apply(lambda x: x[:10]) # '%Y-%m-%d
        del pot['time']

        person_day = pot.pivot_table(rows=['username', 'date'],
            cols='verb',
            aggfunc = len)

        person_day['nevents'] = person_day.sum(axis = 1)
        person_day.reset_index(inplace = True)
        person_day["course_id"] = context.course_id

        return person_day
