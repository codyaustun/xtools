from xtools.mongo.parsers import POTLogParser
from ..collection import CollectionStrategy

class PersonObjectTimeStrategy(CollectionStrategy):
    
    @property
    def name(self):
        return 'derived_person_object_time'

    def create(self, context):
        '''
        Creates a DataFrame that distills the most important information from
        the tracking logs

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
            module_id : str
                Unqiue identifier for modules in a course
            verb : str
                Classification of event type
            time : str
                Timestamp string from the tracking logs
            course_id : str
                edX course id. Ex: 'HarvardX/CB22x/2013_Spring'
            detail : str
                Important details for the event
        '''
        parser = POTLogParser()
        data = context.get('tracking_log', parser=parser)
        data['course_id'] = context.course_id
        return data