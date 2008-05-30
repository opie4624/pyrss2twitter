#!/usr/bin/env python

# System
import os
import sys
import time
import pickle
import urllib, urllib2, httplib
import hashlib
import threading, Queue
# 3rd Party
import twitter
import sqlite3
import memcache
import feedparser

# Constants
DIRECT_MESSAGE_DELAY = 300
RSS_FEED_DELAY = 60

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
#			if self.debug: print "----\nTitle: %s\nStatus: %s" % (e.title, self.canPub(e, False))
			if self.debug: print "----"
			if self.canPub(e):
				if self.debug: print "Title: %s\nStatus: %s" % (e.title, self.canPub(e, False))
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
	


def shorten(url):
	apiUrl = 'http://tweetburner.com/links'
	values = {'link[url]' : url,}
	data = urllib.urlencode(values)
	req = urllib2.Request(apiUrl, data)
	response = urllib2.urlopen(req)
	return response.read()

def blurb(text, length, addDots=True):
	"""Reduces a text to length or less one word at a time, optionally adding..."""
	if len(text) <= length:
		return text
	else:
		(t,u,v) = text.rpartition(' ')
		if addDots is True:
			return '%s...' % blurb(t, length-3, False)
		else:
			return blurb(t, length, False)

class Serializer(threading.Thread):
	def __init__(self, **kwds):
		super(Serializer, self).__init__(**kwds)
		self.setDaemon(1)
		self.workRequestQueue = Queue.Queue()
		self.resultQueue = Queue.Queue()
		self.start()
	
	def apply(self, callable, *args, **kwds):
		"""called by other threads as callable would be"""
		self.workRequestQueue.put((callable, args, kwds))		
		return self.resultQueue.get()
	
	def run(self):
		while 1:
			callable, args, kwds = self.workRequestQueue.get()
			self.resultQueue.put(callable(*args, **kwds))
	

class rss2twitter():
	"""Takes a tuple of RSS feeds and twitter credentials and reads one, posts to the other."""
		
	timers = []
	twitQueue = Serializer()
	twitApi = twitter.Api()
	debug = False
		
	def __init__(self, username, password, feeds=None, cacheDir = './'):
		self.feeds = feeds
		self.twitApi.SetCredentials(username, password)
		self.feedHistory = os.path.join(cacheDir, 'db')
		
		conn = sqlite3.connect(self.feedHistory)
		c = conn.cursor()
		c.execute('''create table if not exists users (username text primary key, title text)''')
		if feeds is not None:
			for f in feeds:
				c.execute('create table if not exists "%s" (hash text primary key, date text)' % hashlib.sha1(f).hexdigest())
		conn.commit()
		c.close()
	
	def doDirectMessages(self, timerIndex):
		"""Process Direct Messages, queue posts"""
		self.timers[timerIndex]=threading.Timer(DIRECT_MESSAGE_DELAY, self.doDirectMessages, (timerIndex,))
		self.timers[timerIndex].start()
	
	def doRSSFeed(self, timerIndex, feedUrl):
		"""Process RSS Feed, queue posts for new items"""
		if self.debug is True:
			print "processing %s" % feedUrl
		feed = feedparser.parse(feedUrl)
		feedtitle = feed.feed.title
		for e in feed.entries:
			posted = False
			if self.wasPublished(hashlib.sha1(feedUrl).hexdigest(), e) is not True:
				tag = "New post from %s" % feedtitle
				link = shorten(e.link)
				txt = "%s: %s: %s [%s]" % (tag, e.title, blurb(e.summary, 140 - (len(e.title) + len(link) + len(tag) + 7)), link)
				if self.debug:
					print "----\n%s" % txt
				else:
					while posted is not True:
						try:
							self.twitQueue.apply(self.twitApi.PostUpdate, txt)
						except urllib2.HTTPError, err:
							errno = int(err.info().items()[0][1][0:3])
							if errno == 401:
								sleep(300)
							elif errno == 502:
								sleep(900)
							elif errno == 503:
								sleep(1800)
							else:
								raise twitter.TwitterError(err.info().items()[0][1])
						else:
							posted = True
		self.timers[timerIndex]=threading.Timer(RSS_FEED_DELAY, self.doRSSFeed, (timerIndex, feedUrl))
		self.timers[timerIndex].start()
	
	def checkDirectMessages(self):
		"""Check for new Direct Messages"""
		pass
	
	def postTweet(self, msgText):
		"""Post a Tweet"""
		pass
	
	def sendDirectMessage(self, msgText):
		"""Send a Direct Message"""
		pass
	
	def deleteDirectMessage(self, msgID):
		"""Delete a DirectMessage"""
		pass
	
	def run(self, doDirect=True, debug=False):
		"""Start processing everything"""
		self.debug = debug
		if doDirect==True:
			self.timers.append(threading.Timer(DIRECT_MESSAGE_DELAY, self.doDirectMessages, (len(self.timers),)))
		if self.feeds is not None:
			for f in self.feeds:
				self.timers.append(threading.Timer(RSS_FEED_DELAY, self.doRSSFeed, (len(self.timers), f)))
		for t in self.timers:
			t.start()
		try:
			self.twitQueue.run()
		except KeyboardInterrupt:
			for t in self.timers:
				t.cancel()
	
	def wasPublished(self, feedTable, feedEntry, storeHistory=True):
		"""Checks to see if a feed item has been previously published"""
		conn = sqlite3.connect(self.feedHistory)
		c = conn.cursor()
		entryVal = hashlib.sha1(feedEntry.summary).hexdigest()
		c.execute('select date from "%s" where hash=?' % feedTable, (entryVal,))
		if len(c.fetchall()) > 0:
			c.close()
			return True
		else:
			if storeHistory is True:
				t = (entryVal, time.time(),)
				c.execute('insert into "%s" values(?, ?)' % feedTable, t)
				conn.commit()
			c.close()
			return False
	
