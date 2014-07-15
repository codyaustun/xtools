import abc
class CollectionsCatalog(dict):
    """
    This is an abstract base class for collection strategy catalogs in 
    order to force all catalogs to provide a basic interface for XData. Catalogs
    are meant to define an initial set of collection strategies in order to 
    promote reuse and extensibility. As such all subclasses must define there 
    own implementation of __init__ which initializes the catalog with strategies
    to use. Once initialized new strategies can be added through the dict 
    interface {collection_name -> strategy}
    """

    @abc.abstractmethod
    def __init__(self):
        """
        Adds initial strategies to the catalog
        """
        message = 'CollectionsCatalog subclasses must reimplement __init__'
        raise NotImplementedError(message)