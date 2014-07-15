from pandas import Series, DataFrame

from .exceptions import MissingDataError

class Collection(object):
    '''
    Collection is a data structure that encapsulates a mongodb collection. 
    Data is loaded lazily, so querys can be built dynamically and mongo will
    only be queried once.
    
    Parameters
    ----------
    xdata : XData
        XData instance for a course
    collection_name : str
        Name of the data collection.
    conditions : dict
        A set of constraints for the results from the collection. The
        default is no constraints
    fields : str Array or array-like object
        A list of fields to return in the results. The default is all fields
    limit : int
        Number of results to return. This can have a considerable effect on 
        the speed of the query. The default is all results.         

    Examples
    --------
    >>> logs = Collection(xdata_instance, 'tracking_logs')
    >>> logs.limit(10)
    >>> logs.conditions({'event_type':'save_problem_check'})
    >>> logs.head() # This fires a query to mongo
    '''
    def __init__(self, xdata, collection_name,
            conditions = {}, limit = 0, fields = []):
        self._xd = xdata
        self.name = collection_name
        self._cached = DataFrame()
        self._conditions = conditions
        self._limit = limit
        self._fields = fields

    def __repr__(self):
        '''
        Returns a string for the name of this collection
        '''
        return self.name

    def __len__(self):
        '''
        Returns the length of dataframe for this collection
        '''
        return len(self.dataframe)

    def __getattr__(self, attribute):
        '''
        Returns the attribute from the dataframe for this collection
        '''
        return getattr(self.dataframe, attribute)

    def __getitem__(self, key):
        '''
        Returns the key from the dataframe for this collection
        '''
        return self.dataframe[key]

    def __setitem__(self, key, value):
        '''
        '''
        self.dataframe[key] = value

    def __delitem__(self, key):
        '''
        '''
        del self.dataframe[key]

    def __contains__(self, key):
        '''
        Returns a boolean for whether or not the key is in the dataframe for
        this collection
        '''
        return key in self.dataframe

    def __getslice__(self, i, j):
        '''
        Returns the slice ([i:j]) from the dataframe for this collection
        '''
        return self.dataframe[i:j]

    def __setslice__(self, i, j, sequence):
        self.dataframe[i:j] = sequence

    def delete_from(self, databases):
        self._xd.delete(self.name, databases, conditions = self._conditions)

    def reset(self, inplace = False):
        if inplace:
            self._conditions = {}
            self._limit = 0
            self._fields = []
            self._cached = DataFrame()
            return self
        else:
            return Collection(self._xd, self.name)

    def find(self, conditions = {}, fields = None, limit = None):
        '''
        Updates the query for mongo

        Parameters
        ----------
        conditions : dict
            A set of constraints for the results that are added to the 
            conditions of the current instance.
        fields : str Array or array-like object
            A list of fields to return in the results. The default is all fields
        limit : int
            Number of results to return. This can have a considerable effect on 
            the speed of the query. The default is all results.

        Returns
        -------
        collection : Collection
            Updated collection with the given parameters
        '''
        new_conditions = self._conditions.copy()
        new_conditions.update(conditions)
        return Collection(self._xd,
            self.name,
            conditions = new_conditions,
            limit = limit if limit else self._limit,
            fields = fields if fields else self._fields[:])

    def limit(self, n):
        '''
        Puts a limit on the query to mongo

        Parameters
        ----------

        Returns
        -------
        
        '''
        return Collection(self._xd,
            self.name,
            conditions = self._conditions.copy(),
            limit = n,
            fields = self._fields[:])

    @property
    def dataframe(self):
        if self._cached.empty:
            if self.exists | (self.name in self._xd.strategies):
                self._cached = self._xd.get(self.name,
                    conditions = self._conditions,
                    limit = self._limit,
                    fields = self._fields)
            else:
                raise MissingDataError(self._xd.course_id, self.name)
        return self._cached

    @property
    def exists(self):
        return not self._xd.fetch(self.name, limit = 1).empty
