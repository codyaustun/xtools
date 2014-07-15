import sys
import datetime
import numpy as np
import scipy as sp
import pandas as pd
import re
from pandas import Series, DataFrame

from ..collection import CollectionStrategy

class FrequencyMatrixStrategy(CollectionStrategy):

    @property
    def name(self):
        return 'derived_frequency_matrix'

    def create(self, context):
        '''
        Create a matrix of browser event counts for every module_id in a course
        for every user

        Parameters
        ----------
        context : XData
            Provides methods for getting any data needed to create the 
            collection defined by this strategy as well as any additional 
            constraints

        Returns
        -------
        data : DataFrame

            Columns
            -------
            username : str
                edX username
            module_id* : int
                Browser event count for the username
        '''
        data = context.get('derived_person_object_time',
            conditions = {'source': 1},
            fields = ['username','module_id'])

        freq_matrix = self.from_data(data).reset_index()
        freq_matrix['course_id'] = context.course_id

        return freq_matrix

    def from_data(self, data):
        '''
        Create a matrix of browser event counts for every module_id in a course
        for every user

        Parameters
        ----------
        data : DataFrame
            username and module id from derived_person_object_time

        Returns
        -------
        freq_matrix : DataFrame

            Columns
            -------
            username : str
                edX username
            module_id* : int
                Browser event count for the username
        '''
        freq_matrix = data.pivot_table(rows = 'username',
           cols = 'module_id',
           aggfunc = len).fillna(0)

        return freq_matrix


