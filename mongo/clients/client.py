import abc

class Client(object):
    '''
    This is an abstact base class for managing Creating, Reading, Updating, and
    Deleting collections from databases to force all managers to satisfy a
    basic interface for XData.
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def collections(self):
        '''
        Provides a list of collections in the current databases

        Returns
        -------
        collection_names : str Array or array-like object
            Contains all the names of the collections in the database
        '''
        pass


    @abc.abstractmethod
    def drop_collection(self, collection_name):
        '''
        Drops the collection with name specified by collection_name

        Parameters
        ----------
        collection_name : str
            Name of the collection
        '''
        pass

    @abc.abstractmethod
    def create(self, data, collection_name):
        '''
        Puts data into the collection specified by collection_name

        Parameters
        ----------
        data : DataFrame

        collection_name : str
            Name of the collection

        '''
        pass

    @abc.abstractmethod
    def read(self, collection_name, conditions={}, fields=[], limit = 0,
            parser = None):
        '''
        Reads data from the collection in the database

        Parameters
        ----------
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
        parser : XParser
            Defines additional munging for raw records. If none, no extra
            parsing will be done.

        Returns
        -------
        df : DataFrame
        '''
        pass

    @abc.abstractmethod
    def update(self, data, collection_name, conditions={}):
        '''
        Replaces documents matching the conditions with the data specified

        Parameters
        ----------
        data : DataFrame

        collection_name : str
            Name of the collection
        conditions : dict
            A set of constraints for the results from the collection. The
            default is no constraints
        '''
        pass

    @abc.abstractmethod
    def delete(self, collection_name, conditions={}):
        '''
        Removes data in the collection matching the conditions dictionary

        Parameters
        ----------
        collection_name : str
            Name of the collection
        conditions : dict
            A set of constraints for the results from the collection. The
            default is no constraints
        '''
        pass


    @abc.abstractmethod
    def connect(self, db):
        '''
        Connects to the database specified by db

        Parameters
        ----------
        db : str
            Name of the database
        '''
        pass