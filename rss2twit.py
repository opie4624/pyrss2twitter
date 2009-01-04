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
#import memcache
import feedparser

# Constants
DIRECT_MESSAGE_DELAY = 300
RSS_FEED_DELAY = 60

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
				if self.debug is True:
					print "creating table for %s" % f
				c.execute('create table if not exists "%s" (hash text primary key, date text)' % hashlib.sha1(f).hexdigest())
		conn.commit()
		c.close()
	
	def doDirectMessages(self, timerIndex):
		"""Process Direct Messages, queue posts"""
		#self.timers[timerIndex]=threading.Timer(DIRECT_MESSAGE_DELAY, self.doDirectMessages, (timerIndex,))
		#self.timers[timerIndex].start()
	
	def doRSSFeed(self, timerIndex, feedUrl):
		"""Process RSS Feed, queue posts for new items"""
		if self.debug is True:
			print "processing %s" % feedUrl
		feed = feedparser.parse(feedUrl)
		feedtitle = feed.feed.title
		for e in feed.entries:
			if self.wasPublished(hashlib.sha1(feedUrl).hexdigest(), e) is not True:
				tag = "New post from %s" % feedtitle
				link = shorten(e.link)
				txt = "%s: %s: %s [%s]" % (tag, e.title, blurb(e.summary, 140 - (len(e.title) + len(link) + len(tag) + 7)), link)
				if self.debug:
					print "----\n%s" % txt
				#self.postTweet(txt)
				threading.Thread(target=self.postTweet, args=(txt,)).start()
		#self.timers[timerIndex]=threading.Timer(RSS_FEED_DELAY, self.doRSSFeed, (timerIndex, feedUrl))
		#self.timers[timerIndex].start()
	
	def checkDirectMessages(self):
		"""Check for new Direct Messages"""
		pass
	
	def postTweet(self, msgText):
		"""Post a Tweet"""
		posted = False
		while posted is not True:
			if self.debug is True:
				print "Queueing tweet %s" % hashlib.sha1(msgText).hexdigest()[0:6]
			try:
				self.twitQueue.apply(self.twitApi.PostUpdate, msgText)
			except HTTPError, err:
				errno = int(err.info().items()[0][1][0:3])
				if errno == 401:
					if self.debug:
						print "Rate limited, sleeping for 5 mins"
					sleep(300)
				elif errno == 502:
					if self.debug:
						print "Server upgrade, sleeping for 15 mins"
					sleep(900)
				elif errno == 503:
					if self.debug:
						print "Server busy, sleeping for 30 mins"
					sleep(1800)
				else:
					raise twitter.TwitterError(err.info().items()[0][1])
			else:
				if self.debug is True:
					print "Tweet %s posted" % hashlib.sha1(msgText).hexdigest()[0:6]
				posted = True
	
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
			if self.debug is True:
				print "Creating first directmessage timer as timer %s" % len(self.timers)
			self.timers.append(threading.Timer(1, self.doDirectMessages, (len(self.timers),)))
		if self.feeds is not None:
			for f in self.feeds:
				if self.debug is True:
					print "Creating first rssfeed timer for %s as timer %s" % (f, len(self.timers),)
				self.timers.append(threading.Timer(1, self.doRSSFeed, (len(self.timers), f)))
		for t in self.timers:
			if self.debug is True:
				print "Starting timer"
			t.start()
	
	def wasPublished(self, feedTable, feedEntry, storeHistory=True):
		"""Checks to see if a feed item has been previously published"""
		conn = sqlite3.connect(self.feedHistory)
		c = conn.cursor()
		entryVal = hashlib.sha1(feedEntry.summary).hexdigest()
		if self.debug is True:
			print "checking %s for published status" % feedEntry.title
		c.execute('select date from "%s" where hash=?' % feedTable, (entryVal,))
		if len(c.fetchall()) > 0:
			c.close()
			if self.debug is True:
				print "published"
			return True
		else:
			if self.debug is True:
				print "unpublished"
			if storeHistory is True:
				if self.debug is True:
					print "storing"
				t = (entryVal, time.time(),)
				c.execute('insert into "%s" values(?, ?)' % feedTable, t)
				conn.commit()
			c.close()
			return False
	
