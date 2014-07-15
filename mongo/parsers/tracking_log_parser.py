from .parser import XParser
import re

class TrackingLogParser(XParser):


    def __init__(self, context):
        self.context = context
        self.hash_map = self.create_hash_map()

    def create_hash_map(self):
        '''
        Returns a dict mapping course URL hashes to dicts of human-readable
        chapter, sequential, vertical, and resource names (and hashes, too).
        Lookups come from the course_structure collection, which is imported 
        from edX each week for each course as course_structure.json.
        
        Parameters:
            course_id: as specified in Mongo, ex: 'HarvardX/CB22x/2013_Spring'
            db: pymongo database reference, ex: pymongo.MongoClient().harvardxdb
        
        '''
        
        # get the course root
        course = self.context._fetch('course_structure',
            conditions = {'content.category': 'course'}).ix[0]
        hash_map = {}  

        def nameFromMetadata(metadata):
            if len(metadata) > 0:
                try: return metadata['display_name'] # for all other categories
                except KeyError: 
                    try: return metadata['discussion_category'] # for category='discussion'
                    except KeyError: return '[Unnamed]'
            else:
                return '[Unnamed]'
        
        # walk through all child hashes: 
        # chapter > sequential > vertical > resource
        for ch_id in course['content']['children']:
            ch = self.context._fetch('course_structure',
                conditions = {'module_id': ch_id}).ix[0]
            ch_hash = ch['module_id'].split('/')[-1]
            try: ch_name = ch['content']['metadata']['display_name']
            except KeyError: ch_name = None
            hash_map[ch_hash] = {'chapter': ch_name,
                                  'sequential': None,
                                  'vertical': None,
                                  'resource': None}
            for seq_id in ch['content']['children']:
                seq = self.context._fetch('course_structure',
                    conditions = {'module_id': seq_id}).ix[0]
                seq_hash = seq['module_id'].split('/')[-1]
                seq_name = seq['content']['metadata']['display_name']
                hash_map[seq_hash] = {'chapter': ch_name,
                                      'sequential': seq_name,
                                      'vertical': None,
                                      'resource': None}
                for vert_id in seq['content']['children']:
                    try: vert = self.context._fetch('course_structure',
                        conditions = {'module_id': vert_id}).ix[0]
                    except IndexError: break # vertical doesn't exist
                    vert_hash = vert['module_id'].split('/')[-1]
                    vert_name = nameFromMetadata(vert['content']['metadata'])
                    hash_map[vert_hash] = {'chapter': ch_name,
                                          'sequential': seq_name,
                                          'vertical': vert_name,
                                          'resource': None}
                    for res_id in vert['content']['children']:
                        try: res = self.context._fetch('course_structure',
                            conditions = {'module_id': res_id}).ix[0]
                        except IndexError: break # resource doesn't exist
                        res_hash = res['module_id'].split('/')[-1]
                        res_name = nameFromMetadata(res['content']['metadata'])
                        hash_map[res_hash] = {'chapter': ch_name,
                                              'sequential': seq_name,
                                              'vertical': vert_name,
                                              'resource': res_name}
        
        # store static tabs, too
        # ex: 'Syllabus', 'Textbook', or 'Data Sets'
        for tab in course['content']['metadata']['tabs']:
            if tab['type'] == 'static_tab':
                hash_map[tab['url_slug']] = tab['name']
        
        # generic tabs in all courses
        hash_map['info'] = 'Course Info'
        hash_map['progress'] = 'Progress'
        hash_map['notes'] = 'My Notes'
        hash_map['open_ended_notifications'] = 'Open Ended Panel'
        hash_map['open_ended_problems'] = 'Open Ended Problems'
        hash_map['peer_grading'] = 'Peer Grading'
        hash_map['instructor'] = 'Instructor'
        hash_map['about'] = 'About'
        
        return hash_map

    def parse(self, doc):
        '''
        Parses an ExperienceAPI/TinCan-esque Activity (actor, verb, object, result, meta)
        from a single JSON-formatted log entry (as a string). Returns a dictionary 
        if activity can be parsed, None otherwise.
        
        Parameters:
            doc: a log item dict (username, time, event_type, etc.)
            hash_map: a dict mapping hashes to human-readable names; use courseHashMap()
            
        '''

        event = str(doc["event"]) # cast to string b/c dict isn't consistent in logs due to truncation
        event_type = doc["event_type"]
        page = doc["page"]
        
        try: e = doc['event']
        except Exception: pass
        
        try: 
            e_get = e['GET']
            e_post = e['POST']
        except Exception:
            pass
        
        # event_result = None
        m = None

        ### VIDEO ###
        if(re_video_play.search(event_type) or re_video_pause.search(event_type)):
            # (note: video_play and video_pause are identical other than the verb name)
            # event_type: [browser] "play_video"
            # event: "{"id":"i4x-HarvardX-CB22x-video-39c9cccdd02846d998ae5cd894830626","code":"YTOR7kAvl7Y","currentTime":279.088,"speed":"1.0"}"
            v = "video_play" if "play_video" == event_type else "video_pause"
            course_obj = getCoursewareObject(event.split("video-")[1].split("'")[0], self.hash_map)
            m = {"youtube_id": e.get('code', None)}
            m["playback_speed"] = e.get("speed", None)
            m["playback_position_secs"] = e.get("currentTime", None)
        elif(re_video_show_transcript.search(event_type) or re_video_hide_transcript.search(event_type)):
            # event_type: [browser] "show_transcript" or "hide_transcript"
            # event: '{"id":"i4x-HarvardX-CB22x-video-ffdbfae1bbb34cd9a610c88349c350ec","code":"IWUv8ltEJOs","currentTime":0}'
            v = "video_show_transcript" if "show_transcript" == event_type else "video_hide_transcript"
            try:
                course_obj = getCoursewareObject(event.split("video-")[1].split("'")[0], self.hash_map)
            except IndexError:
                # two cases in PH207x log where the video id is " "; these appear to be errors
                return None
            # m = {"playback_position_secs": e["currentTime"]}
        elif(re_video_change_speed.search(event_type)):
            # event_type: [browser] "speed_change_video"
            # event: '{"id":"i4x-HarvardX-CB22x-video-a4fc2d96c8354252bb3e405816308828","code":"IERh8MkASDI","current_time":334.4424743652344,"old_speed":"1.50","new_speed":"1.0"}'
            v = "video_change_speed"
            course_obj = getCoursewareObject(event.split("video-")[1].split("'")[0], self.hash_map)
            m = {
                "playback_position_secs": e["current_time"], # note "current_time" is different than "currentTime"!
                "new_playback_speed": e["new_speed"],
                "old_playback_speed": e["old_speed"]
            }
            m["youtube_id"] = e.get("code", None)
        elif(re_video_seek.search(event_type)):
            # event_type: [browser] "seek_video"
            # event: '{"id":"i4x-HarvardX-CB22x-video-2b509bcac67b49f9bcc51b85072dcef0","code":"Ct_M-_bP81k","old_time":641.696984,"new_time":709,"type":"onSlideSeek"}'
            v = "video_seek"
            course_obj = getCoursewareObject(event.split("video-")[1].split("'")[0], self.hash_map)
            m = {}
            try: m["new_playback_position_secs"] = e["new_time"]
            except: m["new_playback_position_secs"] = None
            try: m["old_playback_position_secs"] = e["old_time"]
            except: m["old_playback_position_secs"] = None
            try: m["type"] = e["type"]
            except: m["type"] = None
            try: 
                m["youtube_id"] = e["code"]
            except KeyError:
                m["youtube_id"] = None

        ### SEQUENTIAL ###
        elif(re_seq_goto.search(event_type) or re_seq_next.search(event_type) or re_seq_prev.search(event_type)):
            # (note: seq_goto, seq_prev, and seq_next are identical other than the verb name)
            # when a user navigates via sequential, two events are logged...
            # event_type: [server] "/courses/HarvardX/ER22x/2013_Spring/modx/i4x://HarvardX/ER22x/sequential/lecture_01/goto_position"
            # event_type: [browser] "seq_goto" <-- we use this one
            # event: "{"old":1,"new":2,"id":"i4x://HarvardX/CB22x/sequential/fed323e44ab14407907a7f401f1bfa87"}"
            v = event_type
            try: course_obj = getCoursewareObject(event.split("sequential/")[1].split("'")[0], self.hash_map)
            except IndexError: 
                course_obj = getCoursewareObject(event.split("videosequence/")[1].split("'")[0], self.hash_map) # used in PH207x
            m = {
                "new": e["new"],
                "id": e["id"]
            } 
            try: m["old"] = e["old"] # sometimes the "old" field is missing
            except KeyError: m["old"] = None

        ### POLL ###
        elif(re_poll_view.search(event_type)): 
            # (note: polls are often wrapped by conditionals, but we don't log any events for conditionals)
            # logged when a poll is loaded onscreen (whether answered or not); sometimes several at once
            # event_type: [server] "/courses/HarvardX/ER22x/2013_Spring/modx/i4x://HarvardX/ER22x/poll_question/T13_poll/get_state"
            v = "poll_view"
            course_obj = getCoursewareObject(event_type.split("/")[-2], self.hash_map)
        elif(re_poll_answer.search(event_type)):
            # logged when user clicks a poll answer; "result" field can be 'yes', 'no', or any other answer value
            # event_type: [server] "/courses/HarvardX/ER22x/2013_Spring/modx/i4x://HarvardX/ER22x/poll_question/T7_poll/yes"
            v = "poll_answer"
            split = event_type.split("/")
            course_obj = getCoursewareObject(split[-2], self.hash_map)
            # event_result = split[-1]

        ### PROBLEM (CAPA) ###
        elif(re_problem_view.search(event_type)):
            # logged when a problem is loaded onscreen; often several at once
            # event_type: [server] "/courses/HarvardX/CB22x/2013_Spring/modx/i4x://HarvardX/CB22x/problem/bb8a422a718a4788b174220ed0e9c0d7/problem_get"
            v = "problem_view"
            course_obj = getCoursewareObject(event_type.split("problem/")[1].split("/")[0], self.hash_map)
        elif((re_problem_check.search(event_type) or re_problem_check2.search(event_type)) and doc["event_source"] == "server"):
            # when a user clicks 'Check,' three events are logged...
            # event_type: [browser] "problem_check"
            # event_type: [server] "/courses/HarvardX/CB22x/2013_Spring/modx/i4x://HarvardX/CB22x/problem/249d6f5aa35d4c0e850ece425676eacd/problem_check"
            # event_type: [server] "save_problem_check" OR "problem_check" <-- we use this one b/c event field contains correctness info
            v = "problem_check"
            course_obj = getCoursewareObject(event.split("problem/")[1].split("'")[0], self.hash_map)
            # event_result = event.split("'")[3] # value of key "success"
        elif(re_problem_save_success.search(event_type) or re_problem_save_fail.search(event_type)):
            # when a user clicks 'Save,' three events are logged...
            # event_type: [browser] "problem_save"
            # event_type: [server] "/courses/HarvardX/CB22x/2013_Spring/modx/i4x://HarvardX/CB22x/problem/4c26fb3fcef14319964d818d73cc013d/problem_save"; 
            # event_type: [server] "save_problem_success" OR "save_problem_fail" <-- we use this one to capture success
            v = "problem_save"
            course_obj = getCoursewareObject(event.split("problem/")[1].split("'")[0], self.hash_map)
            # event_result = "success" if event_type.split("problem_")[1] == "save" else "fail"
        elif(re_problem_show_answer.search(event_type)):
            # when a user clicks 'Show Answer', three events are logged...
            # event_type: [browser] "problem_show"
            # event_type: [server] "/courses/HarvardX/CB22x/2013_Spring/modx/i4x://HarvardX/CB22x/problem/2a3fe3442faf4c5ab644768bdad794de/problem_show" <-- we use this
            # event_type: [server] "showanswer" or "show_answer"
            v = "problem_show_answer"
            course_obj = getCoursewareObject(event.split("problem/")[1].split("'")[0], self.hash_map)

        ### WIKI ###
        # TODO: flesh this out with better object names
        elif(re_wiki_view.search(event_type)):
            v = "wiki_view"
            o_name = event_type
            course_obj = {
                "object_type" : "url",
                "object_name" : o_name
            }

        ### ANNOTATION ### (only in CB22x)
        # TODO: annocation_edit and annotation_delete -- requires looking at multiple events at once (difficult with current framework)
        elif(re_annotation_create.search(event_type)):
            # when the user 'Save's an annotation, two events are logged
            # event_type: [server] https://courses.edx.org/courses/HarvardX/CB22x/2013_Spring/notes/api/annotations <-- use this one b/c has post info in event field
            # event_type: [server] https://courses.edx.org/courses/HarvardX/CB22x/2013_Spring/notes/api/annotations/38650 
            v = "annotation_create"
            try:
                s = event.split("uri\\\":\\\"")[1]
                uri = s.split("\\\"")[0]
                o_name = uri
            except Exception:
                o_name = "[Unavailable]" # sometimes the annotation text is too long and the rest gets truncated
            course_obj = {
                "object_type" : "asset_id",
                "object_name" : o_name
            }

        ### BOOK ###
        elif(re_book_view.search(event_type)):
            # we infer book view events from the annotation module, which logs the following every page load:
            # event_type: [server] "/courses/HarvardX/CB22x/2013_Spring/notes/api/search"
            # event: "{"POST": {}, "GET": {"limit": ["0"], "uri": ["/c4x/HarvardX/CB22x/asset/book_sourcebook_herodotus-kyrnos.html"]}}"     
            v = "book_view"
            try:
                s = event.split("uri\": [\"")[1]
                uri = s.split("\"")[0]
                o_name = uri
            except Exception:
                o_name = "[Unavailable]"
            course_obj = {
                "object_type" : "asset_id",
                "object_name" : o_name
            }
        elif(re_book_view_actual.search(event_type)):
            # the actual book module, like the one used in PH207x
            # event_type: [browser] book
            # event: '{"type":"gotopage","old":2,"new":249}' or '{"type":"nextpage","new":3}'
            v = "book_view"
            course_obj = {
                "object_type" : "book_page",
                "object_name" : e["new"]
            }
            m = {e["type"]}

        ### FORUM - TOP LEVEL ###
        elif(re_forum_view.search(event_type)):
            v = "forum_view_home"
            o_name = getHashPath(event_type)
            if(o_name == ""): o_name = None
            course_obj = {
                "object_type" : "forum_hash",
                "object_name" : o_name
            }
            try: 
                m = {
                    "sort_key": e_get["sort_key"][0],
                    "sort_order": e_get["sort_order"][0],
                    "page": e_get["page"][0]
                }
            except KeyError:
                m = None # sometimes there won't be anything in the "event"
        elif(re_forum_view_followed_threads.search(event_type)):
            v = "forum_view_followed"
            o_name = ("".join(event_type.split("users/")[1:]).split("/")[0]) # user id is the trailing number
            course_obj = {
                "object_type" : "forum_user_id",
                "object_name" : o_name
            }
            m = {}
            try: m["sort_key"] = e_get["sort_key"][0]
            except KeyError: m["sort_key"] = None
            try: m["sort_order"] = e_get["sort_order"][0]
            except KeyError: m["sort_order"] = None
            try: m["page"] = e_get["page"][0]
            except KeyError: m["page"] = None
            try: m["group_id"] = e_get["group_id"]
            except KeyError: m["group_id"] = None
        elif(re_forum_view_user_profile.search(event_type)):
            v = "forum_view_user"
            o_name = "".join(event_type.split("users/")[1:]) # user id is the trailing number
            course_obj = {
                "object_type" : "forum_user_id",
                "object_name" : o_name
            }
        elif(re_forum_search.search(event_type)):
            v = "forum_search"
            try: 
                m = {
                    # "text": e_get["text"][0].encode("utf-8"),
                    "sort_key": None,
                    "sort_order": None,
                    "page": None
                }
            except KeyError:
                m = {
                    "sort_key": e_get["sort_key"][0],
                    "sort_order": e_get["sort_order"][0],
                    "page": e_get["page"][0]
                }
                try: m["text"] = e_get["commentable_ids"][0].encode("utf-8"),
                except KeyError: m["text"] = None
            o_name = None
            course_obj = {
                "object_type" : "search_text",
                "object_name" : o_name
            }

        ### FORUM - THREADS ###
        # (note: thread and comment events are coded separately in case we want to break apart later)
        elif(re_forum_thread_create.search(event_type)):
            v = "forum_create_post"
            course_obj = getForumObject(event_type)
        elif(re_forum_thread_close.search(event_type)):
            v = "forum_close"
            course_obj = getForumObject(event_type)
        elif(re_forum_thread_delete.search(event_type)):
            v = "forum_delete"
            course_obj = getForumObject(event_type)
        elif(re_forum_thread_downvote.search(event_type)):
            v = "forum_downvote"
            course_obj = getForumObject(event_type)
        elif(re_forum_thread_flag_abuse.search(event_type)):
            v = "forum_flag_abuse"
            course_obj = getForumObject(event_type)
        elif(re_forum_thread_follow.search(event_type)):
            v = "forum_follow"
            course_obj = getForumObject(event_type)
        elif(re_forum_thread_pin.search(event_type)):
            v = "forum_pin"
            course_obj = getForumObject(event_type)
        elif(re_forum_thread_reply.search(event_type)):
            v = "forum_reply"
            course_obj = getForumObject(event_type)
        elif(re_forum_thread_unflag_abuse.search(event_type)):
            v = "forum_unflag_abuse"
            course_obj = getForumObject(event_type)
        elif(re_forum_thread_unfollow.search(event_type)):
            v = "forum_unfollow"
            course_obj = getForumObject(event_type)
        elif(re_forum_thread_unpin.search(event_type)):
            v = "forum_unpin"
            course_obj = getForumObject(event_type)
        elif(re_forum_thread_unvote.search(event_type)):
            v = "forum_unvote"
            course_obj = getForumObject(event_type)
        elif(re_forum_thread_update.search(event_type)):
            v = "forum_update"
            course_obj = getForumObject(event_type)
        elif(re_forum_thread_upvote.search(event_type)):
            v = "forum_upvote"
            course_obj = getForumObject(event_type)
        elif(re_forum_thread_view_inline.search(event_type)):
            v = "forum_view_inline"
            course_obj = getForumObject(event_type)
        elif(re_forum_thread_view.search(event_type)):
            v = "forum_view_thread"
            course_obj = getForumObject(event_type)

        ### FORUM - COMMENTS ###
        elif(re_forum_comment_delete.search(event_type)):
            v = "forum_delete"
            course_obj = getForumObject(event_type)
        elif(re_forum_comment_downvote.search(event_type)):
            v = "forum_downvote"
            course_obj = getForumObject(event_type)
        elif(re_forum_comment_endorse.search(event_type)):
            v = "forum_endorse"
            course_obj = getForumObject(event_type)
        elif(re_forum_comment_flag_abuse.search(event_type)):
            v = "forum_flag_abuse"
            course_obj = getForumObject(event_type)
        elif(re_forum_comment_reply.search(event_type)):
            v = "forum_reply" 
            course_obj = getForumObject(event_type)
        elif(re_forum_comment_unflag_abuse.search(event_type)):
            v = "forum_unflag_abuse"
            course_obj = getForumObject(event_type)
        elif(re_forum_comment_unvote.search(event_type)):
            v = "forum_unvote"
            course_obj = getForumObject(event_type)
        elif(re_forum_comment_update.search(event_type)):
            v = "forum_update"
            course_obj = getForumObject(event_type)
        elif(re_forum_comment_upvote.search(event_type)):
            v = "forum_upvote"
            course_obj = getForumObject(event_type)

        ### PAGE ### 
        # need to make sure these objects can be found in course axes; otherwise, likely just noise/malformed urls
        elif(re_page_view_courseware.search(event_type)):
            # page_views inside of the courseware look like this...
            # event_type: [server] /courses/HarvardX/ER22x/2013_Spring/courseware/9158300eee2e4eb7a51d5a01ee01afdd/c2dfcb30d6d2490e85b83f882544fb0f/
            v = "page_view"
            path = event_type.split("courseware")[1]
            if(path[-1] == "/"): path = path[:-1]
            try: o_name = self.hash_map[path.split('/')[-1]]
            except KeyError: return None # page is noise b/c not in axis
            course_obj = {
                "object_type" : "courseware_name",
                "object_name" : o_name
            }
        elif(re_page_view_main.search(event_type)):
            # page_views outside of the courseware (top-level tabs) look like this...
            # event_type: [server] /courses/HarvardX/CB22x/2013_Spring/info
            v = "page_view"
            last_item = event_type.split("/")[-1]
            if(last_item == ""): # sometimes has trailing slash
                last_item = event_type.split("/")[-2]
            try: o_name = self.hash_map[last_item]
            except KeyError: return None # if not in our list of tabs, must be noise
            course_obj = {
                "object_type" : "tab_name",
                "object_name" : o_name
            }
        elif(re_page_close.search(event_type)):
            # TODO: how reliable are page_close events within edX and across browsers?
            # page: https://courses.edx.org/courses/HarvardX/CB22x/2013_Spring/courseware/74a6ab26887c474eae8a8632600d9618/7b1ef88acd3743eb922d82781a2371cc/
            # or sometimes: 'https://www.edx.org/courses/HarvardX/CB22x/2013_Spring/courseware/69569a7536674a3c87d9675ddb48f100/a038464de48d45de8d8032c9b6382508/#'
            v = "page_close"
            try: path = page.split("courseware")[1]
            except IndexError:
                # print "page_close IndexError: " + page
                return None # usually: https://courses.edx.org/courses/HarvardX/ER22x/2013_Spring/discussion/forum
            if(len(path) > 0 and path[-1] == "#"): path = path[:-1]
            if(len(path) > 0 and path[-1] == "/"): path = path[:-1]
            try: o_name = self.hash_map[path.split('/')[-1]]
            except KeyError: return None # page is noise b/c not in axis
            course_obj = {
                "object_type" : "courseware_name",
                "object_name" : o_name
            }
            
        else:
            return None

        if(v == "page_view" and o_name == None): return None

        # unicode is the worst
        try: course_obj.update((k, v.encode('utf8', 'replace')) for k, v in course_obj.items())
        except Exception: pass # NoneType
        activity = {
            "username": doc["username"]
            ,"verb": v
            ,"object": course_obj
            # ,"result": event_result
            ,"meta": m
            ,"time": doc["time"]
            ,"module_id": doc.get('module_id', None)
        }
        for k, v in activity.items():
            try: activity[k] = v.encode('utf8', 'replace')
            except Exception: pass # NoneType
        return activity

def getHashPath(s):
    path = "/".join(re_hash.findall(s)).encode("utf-8")
    return path

def getForumObject(event_type):
    # just returning raw hashes for now
    course_obj = {
        "object_type" : "forum_hash",
        "object_name" : getHashPath(event_type)
    }
    return course_obj

def getCoursewareObject(url_name, hash_map):
    # courseware_name format is {chapter}/{sequential}/{vertical}/{resource}
    try: o_name = hash_map[url_name]
    except KeyError: o_name = "[Axis Lookup Failed: " + url_name + "]"
    course_obj = {
        "object_type" : "courseware_name",
        "object_name" : o_name
    }
    return course_obj

# class so not recompiling each time
# all verb regex should be applied to event_type
re_hash = re.compile("[0-9a-f]{24,32}")

re_video_play = re.compile("^play_video$")
re_video_pause = re.compile("^pause_video$")
re_video_show_transcript = re.compile("^show_transcript$")
re_video_hide_transcript = re.compile("^hide_transcript$")
re_video_change_speed = re.compile("^speed_change_video$")
re_video_seek = re.compile("^seek_video$")

re_seq_goto = re.compile("^seq_goto$")
re_seq_next = re.compile("^seq_next$")
re_seq_prev = re.compile("^seq_prev$")

re_poll_view = re.compile("poll_question\/[^/]+\/get_state")
re_poll_answer = re.compile("poll_question\/[^/]+\/(?!get_state).+")

re_problem_view = re.compile("problem\/[^/]+\/problem_get$")
re_problem_save_success = re.compile("^save_problem_success$")
re_problem_save_fail = re.compile("^save_problem_fail$")
re_problem_check = re.compile("^problem_check$") # we want the server event b/c contains correctness info
re_problem_check2 = re.compile("^save_problem_check$") # also needs to be a server event; this is a deprecated event_type
re_problem_show_answer = re.compile("^showanswer$")

re_wiki_view = re.compile("wiki")

re_annotation_create = re.compile("notes\/api\/annotations$") # see POST for object
re_book_view = re.compile("notes\/api\/search$") # used in CB22x; not the normal textbook module
re_book_view_actual = re.compile("^book$")

re_forum_view = re.compile("discussion\/forum$") # view threads
re_forum_view_user_profile = re.compile("discussion\/forum\/users\/[^/]+$")
re_forum_view_followed_threads = re.compile("discussion\/forum\/users\/[^/]+\/followed$")
re_forum_search = re.compile("discussion\/forum\/search$") # also used when selecting from dropdown
re_forum_thread_view_inline = re.compile("discussion\/forum\/[^/]+\/inline$") # view thread from courseware
re_forum_thread_view = re.compile("discussion\/forum\/[^/]+\/threads\/[^/]+$") # retrieve_single_thread (permanent_link_thread)
re_forum_thread_create = re.compile("discussion\/[^/]+\/threads\/create$")
re_forum_thread_close = re.compile("discussion\/threads\/[^/]+/close$")
re_forum_thread_delete = re.compile("discussion\/threads\/[^/]+/delete$")
re_forum_thread_downvote = re.compile("discussion\/threads\/[^/]+/downvote$")
re_forum_thread_flag_abuse = re.compile("discussion\/threads\/[^/]+/flagAbuse$")
re_forum_thread_follow = re.compile("discussion\/threads\/[^/]+/follow$")
re_forum_thread_pin = re.compile("discussion\/threads\/[^/]+/pin$")
re_forum_thread_reply = re.compile("discussion\/threads\/[^/]+/reply$") # create comment
re_forum_thread_unflag_abuse = re.compile("discussion\/threads\/[^/]+/unFlagAbuse$")
re_forum_thread_unfollow = re.compile("discussion\/threads\/[^/]+/unfollow$")
re_forum_thread_unpin = re.compile("discussion\/threads\/[^/]+/unpin$")
re_forum_thread_unvote = re.compile("discussion\/threads\/[^/]+/unvote$")
re_forum_thread_update = re.compile("discussion\/threads\/[^/]+/update$")
re_forum_thread_upvote = re.compile("discussion\/threads\/[^/]+/upvote$")
re_forum_comment_delete = re.compile("discussion\/comments\/[^/]+/delete$")
re_forum_comment_downvote = re.compile("discussion\/comments\/[^/]+/downvote$")
re_forum_comment_endorse = re.compile("discussion\/comments\/[^/]+/endorse$")
re_forum_comment_flag_abuse = re.compile("discussion\/comments\/[^/]+/flagAbuse$")
re_forum_comment_reply = re.compile("discussion\/comments\/[^/]+/reply$")
re_forum_comment_unflag_abuse = re.compile("discussion\/comments\/[^/]+/unFlagAbuse$")
re_forum_comment_unvote = re.compile("discussion\/comments\/[^/]+/unvote$")
re_forum_comment_update = re.compile("discussion\/comments\/[^/]+/update$")
re_forum_comment_upvote = re.compile("discussion\/comments\/[^/]+/upvote$")

re_page_view_courseware = re.compile("courseware\/[^/]+([^/]+)*\/?")
re_page_view_main = re.compile("courses\/[^/]+\/[^/]+\/[^/]+\/[^/]+") # very general, run after everything else
re_page_close = re.compile("^page_close$")