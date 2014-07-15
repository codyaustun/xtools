import sys
import datetime
import math
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import pandas as pd
from pandas import Series, DataFrame

from .exceptions import MissingDataError
from .exceptions import MissingStrategyError

from .collection import Collection
from ..munge.logger import Logger
from .clients.client import Client
from .catalogs.collections_catalog import CollectionsCatalog

from ..munge.logger import ArrayLogger
from .catalogs.derived_collections import DerivedCollectionsCatalog
from .clients.mongo_client import MongoClient

class XData:
    """
    XData employs the recursive polymorphic factory design pattern in order to 
    provide flexibility and extensibility in fetching and creating data in the 
    MITx and HarvardX mongodb instance
    """
    def __init__(self, course_id, read_from, write_to = [],
            logger = ArrayLogger(),
            catalog = DerivedCollectionsCatalog(),
            client = MongoClient()):
        '''
        Data Structure charged with getting the data requested from the catalog
        by any means necessary. If the requested data can't be found in any of 
        the read_from databases, it will compute the data on the fly using raw 
        data.

        Parameters
        ----------
        course_id : str 
            The course_id as specified by edX for the desired course
        read_from : str Array or array-like object
            Database names to search through. XData will search through 
            the databases in order and return the results from the first 
            database that has the requested data.
        write_to : str Array or array-like object
            Database names where data is written to if data is computed 
            while fulfulling a request. No data is written if empty.
        logger : Logger
            Records the processes of XData. The default is a PrintLogger.
        catalog : CollectionsCatalog
            Container for the strategies used to build collections. Defaults to
            a DerivedCollectionsCatalog.
        client : Client
            Responsible for storing and fetching collections from the databases.
            The default is a MongoClient.
        '''
        self._course_id = course_id

        assert isinstance(catalog, CollectionsCatalog), \
            'catalog must be an instance of CollectionsCatalog or a subclass'
        self.catalog = catalog
        assert isinstance(logger, Logger),  \
            'logger must be an instance of Logger or a subclass'
        self.logger = logger
        assert isinstance(client, Client), \
            'client must be an instance of Client or a subclass'
        self.client = client

        self._read_from = read_from
        self._write_to = write_to
        self._cached_collections = {}
        self._computing = set() # Used to prevent infinite loops

    @property
    def course_id(self):
        return self._course_id

    @course_id.setter
    def course_id(self, value):
        self.clear()
        self._course_id = value

    @property
    def strategies(self):
        '''
        List of the collections that can be generated with the current
        CollectionsCatalog

        Returns
        -------
        strategies : list
            List of strings
        '''
        return self.catalog.keys()

    @property
    def fetchable(self):
        '''
        Lists of all the collections that have data for the course

        Returns
        -------
        collections : list
            List of Collections
        '''
        existing = set()
        for db in self._read_from:
            self.client.connect(db)
            existing.update(self.client.collections())

        fetchable = []
        for collection_name in existing:
            collection = Collection(self, collection_name)
            if collection.exists:
                fetchable.append(collection)

        return fetchable

    def __getitem__(self, collection_name):
        '''
        Retrieves records pretaining to the course from the first read_from 
        database with data. If no data exists in any of the read_from databases,
        it will be generated from the catalog and saved to the write_to 
        databases.

        Parameters
        ----------
        collection_name : str
            Name of the data collection.

        Returns
        -------
        collection : Collection
        '''
        return self._create_collection(collection_name)

    def __setitem__(self, collection_name, data):
        '''
        Stores a collection of data in the write_to databases under the
        collection_name

        Parameters
        ----------
        data : DataFrame
            Data to be stored
        collection_name : str
            Name for the collection to be stored under
        '''
        data['course_id'] = self.course_id
        self.store(data, collection_name)



    def __getattr__(self, collection_name):
        '''
        Retrieves records pretaining to the course from the first read_from 
        database with data. If no data exists in any of the read_from databases,
        it will be generated from the catalog and saved to the write_to 
        databases.

        Parameters
        ----------
        collection_name : str
            Name of the data collection.

        Returns
        -------
        collection : Collection
        '''
        return self._create_collection(collection_name)

    def clear(self):
        '''
        Clears cached collections
        '''
        self._cached_collections = {}


    def get(self, collection_name, conditions = {}, fields = [], limit = None,
            parser = None, mongo_id = False):
        '''
        Retrieves records pretaining to the course from the first read_from 
        database with data. If no data exists in any of the read_from databases,
        it will be generated from the catalog and saved to the write_to 
        databases.

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
        mongo_id : boolean
            Determines whether or not to include Mongo Object id "_id"

        Returns
        -------
        df : DataFrame
        '''
        # Try to read data from the list of read_from database
        df = self.fetch(\
            collection_name,
            conditions = conditions,
            fields = fields,
            limit = limit,
            parser = parser,
            mongo_id = mongo_id)

        # If the requested data didn't exist in any of the databases, XData will
        # try to create it
        if df.empty:
            # OPTIMIZE: Make it so the entire collection doesn't need to be in
            #   memory
            # Creates collection in all write_to databases
            collection = self.compute(collection_name)

            # Stores the created collection in the write_to databases
            self.store(collection, collection_name)

            # Tries to fetch the data again.
            df = self.fetch(\
                collection_name,
                conditions = conditions,
                fields = fields,
                limit = limit,
                parser = parser,
                mongo_id = mongo_id)

        return df


    def compute(self, collection_name):
        '''
        Computes a collection of data using the strategy under the 
        collection_name in the catalog 

        Parameters
        ----------
        collection_name : str
            Name of the data collection.

        Returns
        -------
        df : DataFrame
        '''
        
        self.logger.log('Computing {0}'.format(collection_name))
        try:
            data = self.catalog[collection_name].create(self)
        except KeyError as e:
            if e.message == collection_name:
                raise MissingStrategyError(collection_name, self.catalog)
            else:
                raise e

        self.logger.log('Created {0}'.format(collection_name))
        return data

    def store(self, data, collection_name):
        '''
        Stores a collection of data in the write_to databases under the
        collection_name

        Parameters
        ----------
        data : DataFrame
            Data to be stored
        collection_name : str
            Name for the collection to be stored under
        '''
        self.logger.log("Storing {0}".format(collection_name))
        for db in self._write_to:
            self.client.connect(db)
            self.logger.log('{0} saving to db.{1}'.format(collection_name, db))
            self.client.create(data, collection_name)
            self.logger.log('{0} saved to db.{1}'.format(collection_name, db))

    def fetch(self, collection_name, conditions = {}, fields = [], limit = None,
            parser = None, mongo_id = False):
        df = DataFrame()
        '''
        Wrapper around the manger's pull method that iterates through the
        read_from databases until it gets results. The course_id is specified as
        an additional condition to the client pull method.
        '''
        self.logger.log("Attempting to fetch {0}".format(collection_name))
        # Look through the read from database for the desired data
        for db in self._read_from:
            # Check for data in db
            message = "Looking for data for {0} in {1} from db.{2}".format(\
                self.course_id,
                collection_name,
                db)
            self.logger.log(message)

            # Try to fetch data
            self.client.connect(db)
            conditions['course_id'] = self.course_id
            df = self.client.read(collection_name,
                conditions = conditions,
                fields = fields,
                limit = limit,
                parser = parser,
                mongo_id = mongo_id
                )
            if df.empty:
                # If there isn't data, the remaining read_from databases are 
                #   tried
                message = "No data for {0} found in {1} from db.{2}".format(\
                    self.course_id,
                    collection_name,
                    db)
                self.logger.log(message)
            else:
                # If there is data, df is set to that and no further searching
                #   is required
                message = "Found data in {0} from db.{1}".format(\
                    collection_name,
                    db)
                self.logger.log(message)
                break
        return df

    def delete(self, collection_name, databases, conditions = {}):
        conditions['course_id'] = self.course_id
        for db in databases:
            self.client.connect(db)
            self.client.delete(collection_name, conditions)

    def _create_collection(self, collection_name):
        collection = None
        if collection_name in self._cached_collections:
            collection = self._cached_collections[collection_name]
        else:
            collection = Collection(self, collection_name)
            self._cached_collections[collection_name] = collection
        return collection









            


        

        