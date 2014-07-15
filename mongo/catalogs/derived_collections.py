from .collections_catalog import CollectionsCatalog
from ..strategies.collection import CollectionStrategy
from ..strategies.derived import *

class DerivedCollectionsCatalog(CollectionsCatalog):

    def __init__(self):
        '''
        Initializes a catalog containing instances of all strategies for making 
        derived data collections as defined by mongo.collections.derived
        '''
        for subclass in CollectionStrategy.__subclasses__():
            instance = subclass()
            self.__setitem__(instance.name, instance)