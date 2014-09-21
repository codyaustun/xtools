import re

# Known log_patterns for verb
verb_patterns = [\
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