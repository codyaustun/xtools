import sys
import datetime
import numpy as np
import scipy as sp
import pandas as pd
import re
from pandas import Series, DataFrame

from ..collection import CollectionStrategy
from ...parsers.parser import XParser

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

# FIX: This doesn't need to be a class. Change it to a function.
class POTLogParser(XParser):
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
        for pattern in log_patterns:
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

# Known log_patterns for verb
log_patterns = [\
    ### VIDEO ###
    {'verb': 'video_play','regex': re.compile("^play_video$")},
    {'verb': 'video_pause','regex': re.compile("^pause_video$")},
    {'verb': 'video_show_transcript','regex': re.compile("^show_transcript$")},
    {'verb': 'video_hide_transcript','regex': re.compile("^hide_transcript$")},
    {'verb': 'video_change_speed','regex': re.compile("^speed_change_video$")},
    {'verb': 'video_seek','regex': re.compile("^seek_video$")},

    ### SEQUENTIAL ###
    {'verb': 'seq_goto','regex': re.compile("^seq_goto$")},
    {'verb': 'seq_next','regex': re.compile("^seq_next$")},
    {'verb': 'seq_prev','regex': re.compile("^seq_prev$")},

    ### POLL ###
    {'verb': 'poll_view','regex': re.compile("poll_question\/[^/]+\/get_state")},
    {'verb': 'poll_answer','regex': re.compile("poll_question\/[^/]+\/(?!get_state).+")},

    ### PROBLEM (CAPA) ###
    {'verb': 'problem_view','regex': re.compile("problem\/[^/]+\/problem_get$")},
    {'verb': 'problem_check','regex': re.compile("^problem_check$")},
    {'verb': 'problem_save','regex': re.compile("^save_problem_check$")},
    {'verb': 'problem_save_success','regex': re.compile("^save_problem_success$")},
    {'verb': 'problem_save_fail','regex': re.compile("^save_problem_fail$")},
    {'verb': 'problem_show_answer','regex': re.compile("^showanswer$")},

    ### WIKI ###
    {'verb': 'wiki_view','regex': re.compile("wiki")},

    ### ANNOTATION ### (only in CB22x)
    {'verb': 'annotation_create','regex': re.compile("notes\/api\/annotations$")},

    ### BOOK ###
    {'verb': 'book_view','regex': re.compile("notes\/api\/search$")},
    {'verb': 'book_view','regex': re.compile("^book$")},

    ### FORUM - TOP LEVEL ###
    {'verb': 'forum_view_home','regex': re.compile("discussion\/forum$")},
    {'verb': 'forum_view_followed','regex': re.compile("discussion\/forum\/users\/[^/]+\/followed$")},
    {'verb': 'forum_view_user','regex': re.compile("discussion\/forum\/users\/[^/]+$")},
    {'verb': 'forum_search','regex': re.compile("discussion\/forum\/search$")},

    ### FORUM - THREADS ###
    {'verb': 'forum_create_post','regex': re.compile("discussion\/[^/]+\/threads\/create$")},
    {'verb': 'forum_close','regex': re.compile("discussion\/threads\/[^/]+/close$")},
    {'verb': 'forum_delete','regex': re.compile("discussion\/threads\/[^/]+/delete$")},
    {'verb': 'forum_downvote','regex': re.compile("discussion\/threads\/[^/]+/downvote$")},
    {'verb': 'forum_flag_abuse','regex': re.compile("discussion\/threads\/[^/]+/flagAbuse$")},
    {'verb': 'forum_follow','regex': re.compile("discussion\/threads\/[^/]+/follow$")},
    {'verb': 'forum_pin','regex': re.compile("discussion\/threads\/[^/]+/pin$")},
    {'verb': 'forum_reply','regex': re.compile("discussion\/threads\/[^/]+/reply$")},
    {'verb': 'forum_unflag_abuse','regex': re.compile("discussion\/threads\/[^/]+/unFlagAbuse$")},
    {'verb': 'forum_unfollow','regex': re.compile("discussion\/threads\/[^/]+/unfollow$")},
    {'verb': 'forum_unpin','regex': re.compile("discussion\/threads\/[^/]+/unpin$")},
    {'verb': 'forum_unvote','regex': re.compile("discussion\/threads\/[^/]+/unvote$")},
    {'verb': 'forum_update','regex': re.compile("discussion\/threads\/[^/]+/update$")},
    {'verb': 'forum_upvote','regex': re.compile("discussion\/threads\/[^/]+/upvote$")},
    {'verb': 'forum_view_inline','regex': re.compile("discussion\/forum\/[^/]+\/inline$")},
    {'verb': 'forum_view_thread','regex': re.compile("discussion\/forum\/[^/]+\/threads\/[^/]+$")},

    ### FORUMS - COMMENTS ###
    {'verb': 'forum_delete','regex': re.compile("discussion\/comments\/[^/]+/delete$")},
    {'verb': 'forum_downvote','regex': re.compile("discussion\/comments\/[^/]+/downvote$")},
    {'verb': 'forum_endorse','regex': re.compile("discussion\/comments\/[^/]+/endorse$")},
    {'verb': 'forum_flag_abuse','regex': re.compile("discussion\/comments\/[^/]+/flagAbuse$")},
    {'verb': 'forum_reply','regex': re.compile("discussion\/comments\/[^/]+/reply$")},
    {'verb': 'forum_unflag_abuse','regex': re.compile("discussion\/comments\/[^/]+/unFlagAbuse$")},
    {'verb': 'forum_unvote','regex': re.compile("discussion\/comments\/[^/]+/unvote$")},
    {'verb': 'forum_update','regex': re.compile("discussion\/comments\/[^/]+/update$")},
    {'verb': 'forum_upvote','regex': re.compile("discussion\/comments\/[^/]+/upvote$")},

    ### PAGE ###
    {'verb': 'page_view_courseware','regex': re.compile("courseware\/[^/]+([^/]+)*\/?")},
    {'verb': 'page_view_main','regex': re.compile("courses\/[^/]+\/[^/]+\/[^/]+\/[^/]+")},
    {'verb': 'page_close','regex': re.compile("^page_close$")},
]