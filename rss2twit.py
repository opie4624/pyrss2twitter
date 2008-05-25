#!/usr/bin/env python

# python rss reader -> twitter post
import feedparser, pickle, os, sys, twitter, urllib, urllib2, hashlib

class rss2twit:
	def __init__(self, feedurl, username, password, filepath = './', feedtag = "", debug=False):
		self.filepath = filepath
		self.feedurl = feedurl
		self.twit = twitter.Api()
		self.debug = debug
		self.feedtag = feedtag
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
			if self.debug: print "----\nTitle: %s\nStatus: %s" % (e.title, self.canPub(e, False))
			if self.canPub(e):
				elink = self.shorten(e.link)
				if self.feedtag == False:
					txt = ("%s: %s [%s]" % (e.title, self.blurb(e.summary, 140 - (len(e.title) + len(elink) + 5)), elink))
				else:
					if self.feedtag == '':
						self.feedtag = "New post from %s" % self.feedtitle
					txt = ("%s: %s: %s [%s]" % (self.feedtag, e.title, self.blurb(e.summary, 140 - (len(e.title) + len(elink) + len(self.feedtag) + 7)), elink))
				if self.debug: print "Tweeting: %s" % txt
				s = self.twit.PostUpdate(txt)
				if self.debug: print "Status: %s" % s.text
				p += 1
		if self.debug: print "Published: %s\nOld: %s\nTotal: %s" % (p, len(entries) - p, len(entries))
	
	def canPub (self, entry, store=True):
		entryVal = hashlib.sha1(entry.summary).hexdigest()
		if self.entryCache.has_key(entryVal):
			return False
		else:
			if store==True:
				self.entryCache[entryVal] = entry.link
				pickle.dump(self.entryCache, file(self.filepath, 'w+b'))
			return True
	
	def shorten(self, url):
 		apiUrl = 'http://tweetburner.com/links'
		values = {'link[url]' : url,}
		data = urllib.urlencode(values)
		req = urllib2.Request(apiUrl, data)
		response = urllib2.urlopen(req)
		return response.read()
		
	def blurb(self, text, length, addDots = True):
		"""Shorten's text to length by words"""
		if len(text) < length:
			return text
		else:
			(t,u,v) = text.rpartition(' ')
			if addDots == True:
				return self.blurb(t, length - 3, False) + "..."
			else:
				return self.blurb(t, length, False)
	
	def go(self):
		entries = self.getFeed()
		self.postTweet(entries)
	

