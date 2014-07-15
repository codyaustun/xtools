import pandas as pd
import pymongo
import json
import getpass

from .client import Client

class MongoClient(Client):
    """MongoClient is subclass of Client for interacting with mongodb"""

    def __init__(self):
        '''
        Grabs the current user's username and connects to their personal
        database
        '''
        db = getpass.getuser()
        self.connect(db)

    def collections(self, include_system_collections=False):
        '''
        Provides a list of collections in the current databases

        Returns
        -------
        collection_names : str Array or array-like object
            Contains all the names of the collections in the database
        '''
        tmp = include_system_collections
        return self._mdb.collection_names(include_system_collections = tmp)

    def create_collection(self, collection_name):
        '''
        Creates a collection with name specified by collection_name

        Parameters
        ----------
        collection_name : str
            Name of the collection
        '''
        self._mdb.create_collection(collection_name)

    def drop_collection(self, collection_name):
        '''
        Drops the collection with name specified by collection_name

        Parameters
        ----------
        collection_name : str
            Name of the collection
        '''
        collection = getattr(self._mdb, collection_name)
        collection.drop()



    def create(self, data, collection_name):
        '''
        Puts data into the collection specified by collection_name. Note that
        the data's index will not be saved in the database.

        Parameters
        ----------
        data : DataFrame

        collection_name : str
            Name of the collection
        '''
        # generator version
        def df_chunks(df,n):
            '''
            Yield successive n-sized chunks from a dataframe.
            
            ### If you want a rough memory estimate of an object (dataframe slice):
            
            import sys
            sys.getsizeof(obj)
            '''
            
            #Check that data is larger than chunk size
            if n <= len(df):
                ti = 0  #TOTAL INSERTED DOCS
                while ti+n<=len(df):
                    yield json.loads(df.iloc[ti:ti+n,:].to_json(orient='records'))
                    ti += n
                    #print ti,ti+n
                
                #Catch Remainder
                yield json.loads(df.iloc[ti:len(df),:].to_json(orient='records'))
                #print ti,len(df)
          
            else:
                yield json.loads(df.to_json(orient='records')) 
        
        collection = getattr(self._mdb, collection_name)
        for records in df_chunks(data,1000):
            collection.insert(records)

    def read(self, collection_name, conditions={}, fields=[], limit = 0,
            parser = None, mongo_id = False):
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
        mongo_id : boolean
            Determines whether or not to include Mongo Object id "_id"

        Returns
        -------
        df : DataFrame
        '''
        data = self._pull(collection_name,
            conditions = conditions,
            fields = fields,
            limit = limit,
            parser = parser)
    
        df = pd.DataFrame.from_records(data)

        if (not df.empty) & ('_id' in df) & (not mongo_id):
            del df['_id']
        return df

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
        # Delete old values 
        self.delete(collection_name, conditions = conditions)

        # insert new data
        self.create(data, collection_name)

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
        # Get collection data
        collection_connection = getattr(self._mdb,collection_name)
        query_cursor = collection_connection.find(conditions, fields = '_id')
            
        # Remove records specified by query
        for doc in query_cursor:
            collection_connection.remove(doc)

    def _pull(self, collection_name, conditions={}, fields=[], limit = None,
            parser = None):
        # Get collection object
        collection_connection = getattr(self._mdb,collection_name)
        
        # Create query
        params = {} if len(fields) == 0 else {'fields': fields}
        if limit:
            params['limit'] = limit
        query_cursor = collection_connection.find(conditions, **params)
            
        # Get all records/documents
        data=[]
        for doc in query_cursor:
            # Each doc is a dict, meaning docs is a list of docs
            if parser:
                doc = parser.parse(doc)
            if doc:
                data.append(doc)

        return data

    def connect(self, db):
        '''
        Connects to the database specified by db

        Parameters
        ----------
        db : str
            Name of the database
        '''
        self.db = db
        self._connection = pymongo.MongoClient()
        self._mdb = getattr(self._connection, self.db) # pymongo Database
        
