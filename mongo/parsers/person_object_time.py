import numpy as np

from xtools.mongo.parsers import Parser
from .log_patterns import verb_patterns

# FIX: This doesn't need to be a class. Change it to a function.
class POTLogParser(Parser):
    def parse(self, doc):
        '''
        Parses an ExperienceAPI/TinCan-esque Activity (actor, verb, object, result, meta)
        from a single JSON-formatted log entry (as a string). Returns a dictionary 
        if activity can be parsed, None otherwise.
        
        Parameters:
        -----------
        doc : dict
            a log item dict (username, time, event_type, etc.)

        Returns:
        --------
        activity : dict
            parsed log item
        '''
        # Some logs in 6.002x Spring_2013 didn't have event_type
        try:
            event_type = doc["event_type"]
        except KeyError as e:
            return None

        verb = None

        # Extracting the patterns for event_types out of this function clarifies
        #   the code and allows for easy additions and modifications to the
        #   patterns.
        for pattern in verb_patterns:
            if pattern['regex'].search(event_type):
                verb = pattern['verb']
                break

        # If the verb wasn't found in our patterns, we ignore it.
        if not verb:
            return None

        activity = {
            "username": doc["username"],
            "verb": verb,
            "time": doc["time"],
            "module_id": doc.get('module_id', np.NaN),
            'source': 0 if doc['event_source'] == 'server' else 1
        }

        # Problem modules can contain multiple parts, which are all graded in a 
        #   single problem_check or problem_save event. In order to know the
        #   correctness of an answer, the 'correct_map' needs to be parsed for 
        #   'correct' and 'partially-correct' parts
        if (verb == 'problem_save') | (verb == 'problem_check'):
            if doc['event_source'] == 'server':
                correct_map = doc['event']['correct_map']
                total = 0.0
                correct = 0.0
                for key, val in correct_map.iteritems():
                    total += 1.
                    if val['correctness'] == 'correct':
                        correct += 1.
                    elif val['correctness'] == 'partially-correct':
                        correct += 0.5
                if total > 0:
                    correct = correct / total
                    activity['detail'] = {'correct': correct}

        for k, v in activity.items():
            try: activity[k] = v.encode('utf8', 'replace')
            except Exception: pass # NoneType
        return activity

