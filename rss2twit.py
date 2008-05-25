#!/usr/bin/env python

# python rss reader -> twitter post
import feedparser, pickle, os, sys, twitter, urllib, urllib2, hashlib

class rss2twit:
	def __init__(self, feedurl, username, password, filepath = './', feedtag = "", debug=False):
		self.filepath = filepath
		self.feedurl = feedurl
		self.twit = twitter.Api()
		self.debug = debug
		self.feedtitle = ''
		
		self.twit.SetCredentials(username, password)	
		if os.path.isdir(self.filepath):
			self.filepath = os.path.join(self.filepath, hashlib.sha1(self.feedurl).hexdigest())
		if os.path.exists(self.filepath):
			self.entryCache = pickle.load(file(self.filepath, 'r+b'))
		else:
			self.entryCache = {} 
	
	def getFeed(self, limit = 0):
		feed = feedparser.parse(self.feedurl);
		self.feedtitle = feed.feed.title
		e = feed.entries
		if limit > 0:
			e = e[0:limit]
		return e
	
# post format: Tag: title - blurb... [url]
	def postTweet(self, entries):
		p = 0
		for e in entries:
			if self.isEntPub(e):
				if debug: print "----\n"
				if self.feedtag == False:
					txt = ("%s - %s [%s]" % e.title, blurb(e.value), shorten(e.link))
				else:
					if self.feedtag == '':
						self.feedtag = "New post from %s" % self.feedtitle
					txt = ("%s: %s - %s [%s]" % e.feedtag, e.title, blurb(e.value), shorten(e.link))
				if debug: print "Tweeting: %s" % txt
				s = self.twit.PostUpdate(txt)
				if debug: print "Status: %s" % s.text
				p += 1
		if debug: print "Published: %s\nOld: %s\nTotal: %s" % p, len(entries) - p, len(entries)
	
	def isEntPub (self, entry):
		entryVal = hashlib.sha1(entry.value).hexdigest()
		if self.entryCache.has_key(entryVal):
			return True
		else:
			self.entryCache[entryVal] = entry.link
			pickle.dump(self.entryCache, file(self.filepath, 'w+b'))
			return False
	
	def shorten(self, url):
 		apiUrl = 'http://tweetburner.com/links'
		values = {'link[url]' : url,}
		data = urllib.urlencode(values)
		req = urllib2.Request(apiUrl, data)
		response = urllib2.urlopen(req)
		return response.read()
	
	def go():
		entries = getFeed(2)
		postTweet(entries)
	

