import abc
class CollectionStrategy(object):
    """
    This abstract base class is for various collection generation strategies 
    enforces all strategies to satisfy a basic interface for XData
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def name(self):
        """
        String representing the name of the collection generated by this 
        strategy
        """
        pass

    @abc.abstractmethod
    def create(self, context):
        """
        Defines the algorithm for creating the collection

        Parameters
        ----------
        context : XData
            Provides methods for getting any data needed to create the 
            collection defined by this strategy as well as any additional 
            constraints

        Returns
        -------
        data : DataFrame
        """
        pass