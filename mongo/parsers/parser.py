import abc

class XParser(object):
    '''
    This is an absract base class for XData parsers to ensure all parsers
    provide the required interface
    '''
    __metaclass__ = abc.ABCMeta


    @abc.abstractproperty
    def parse(self, doc):
        '''
        Parse individual records from the database
        '''
        pass