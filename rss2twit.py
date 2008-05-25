#!/usr/bin/env python

# python rss reader -> twitter post
import feedparser, pickle, os, sys, twitter, urllib, urllib2, hashlib

class rss2twit:
	def __init__(self, feedurl, username, password, filepath = './', feedtag = "", debug=False):
		self.filepath = filepath
		self.feedurl = feedurl
		self.twit = twitter.Api()
		self.debug = debug
		
		self.twit.SetCredentials(username, password)	
		if (os.path.isdir(self.filepath)):
			self.filepath = os.path.join(self.filepath, hashlib.sha1(self.feedurl).hexdigest())
		if os.path.exists(self.filepath):
			self.itemcache = pickle.load(file(self.filepath, 'r+b'))
		else:
			self.itemcache = {} 
	
# TODO 
	def getLatestFeedItems(self, itemLimit = 0):
		pass
#		feed=feedparser.parse(self.feedurl);
#		it=feed["items"]
#		if(itemLimit > 0):
#			it=it[0:itemLimit]
#		return it

# TODO 
	def twitIt(self, items):
		pass
#		pItems=0
#		for it in items:
#			if self.itemPublished(it) == None:
#				print "----\n"
#				txt=it["title"] +" "+self.tiny(it["link"])
#				print txt
#				status = self.twApi.PostUpdate(txt)
#				print "status: ", status.text
#				pItems=pItems+1
#		print "Total items: ", len(items)
#		print "published: ",pItems
#		print "old stuff: ",len(items) - pItems

# TODO
	def itemPublished (self, item):
		pass

# TODO 
	def tiny(self, url):
 		pass