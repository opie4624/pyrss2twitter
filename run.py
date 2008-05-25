#!/usr/bin/env python

import rss2twit

forums = rss2twit.rss2twit('http://uhacc.org/forums/forum-rss.php', 'uhacc', 'oz8(Kaki', feedtag='New Forums Post', debug=True)
sysblogd = rss2twit.rss2twit('http://www.uhacc.org/gl_sysblogd/backend/sysblogd.rss', 'uhacc', 'oz8(Kaki', feedtag='', debug=True)
#talkshoe = rss2twit.rss2twit('http://www.uhacc.org/gl_sysblogd/backend/sysblogd.rss', 'uhacc', 'oz8(Kaki', feedtag='New Forums Post', debug=True)

forums.go()
sysblogd.go()
#talkshoe.go()
