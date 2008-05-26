#!/usr/bin/env python

import rss2twit
import twitter
import os
import pickle

if os.path.exists('userlist'):
        userdb = pickle.load(file('userlist', 'r+b'))
else:
        userdb = {} 

forums = rss2twit.rss2twit('http://uhacc.org/forums/forum-rss.php', 'uhacc', 'oz8(Kaki', feedtag='New Forums Post', debug=True)
sysblogd = rss2twit.rss2twit('http://www.uhacc.org/gl_sysblogd/backend/sysblogd.rss', 'uhacc', 'oz8(Kaki', feedtag='', debug=True)
#talkshoe = rss2twit.rss2twit('http://www.uhacc.org/gl_sysblogd/backend/sysblogd.rss', 'uhacc', 'oz8(Kaki', feedtag='New Forums Post', debug=True)

forums.go()
sysblogd.go()
#talkshoe.go()

twit = twitter.Api()
twit.SetCredentials('uhacc', 'oz8(Kaki')

gd = twit.GetDirectMessages()

for m in gd:
	if userdb[m.sender_screen_name] == 'Banned':
		print "Received message ("+ m.text +") from banned member "+ m.sender_screen_name + ", deleting."
		twit.DestroyDirectMessage(m.id)
	elif userdb[m.sender_screen_name] == 'Passive Member':
		print "Received message ("+m.text+") from passive member "+ m.sender_screen_name +", sending note and deleting."
		twit.PostDirectMessage(m.sender_screen_name, 'Sorry, only Full Members can make announcements.  http://twurl.nl/hqlm5t for membership details.')
		twit.DestroyDirectMessage(m.id)
	else:
		print "Received message ("+m.text+") from member "+m.sender_screen_name+"."
		twit.PostUpdate(userdb[m.sender_screen_name]+" @"+m.sender_screen_name+" says: " + forums.blurb(m.text, 9+len(userdb[m.sender_screen_name])+len(m.sender_screen_name)))
		print "Tweeting: "+userdb[m.sender_screen_name]+" @"+m.sender_screen_name+" says: " + forums.blurb(m.text, 9+len(userdb[m.sender_screen_name])+len(m.sender_screen_name))
		twit.DestroyDirectMessage(m.id)
