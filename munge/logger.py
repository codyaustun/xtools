from datetime import datetime, timedelta
from pprint import pprint
import abc

class Logger(object):
    """docstring for Logger"""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def log(self, message):
        pass
        
class PrintLogger(Logger):
    """docstring for PrintLogger"""
    def __init__(self):
        self.start_time = datetime.now()

    def log(self, message):
        print datetime.now() - self.start_time, message

class ArrayLogger(Logger):
    ''' docstring for ArrayLogger '''
    def __init__(self, size = 100):
        self.start_time = datetime.now()
        self.logs = []
        self.size = size

    def log(self, message):
        timed_message = "{0}: {1}".format((datetime.now() - self.start_time),
            message)
        if len(self.logs) >= self.size:
            self.logs.pop(0)
        self.logs.append(timed_message)

