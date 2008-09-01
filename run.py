#!/usr/bin/env python

from rss2twit import rss2twitter

# Two feeds, Default tag of "New post from FeedTitle"
#instance1 = rss2twitter('twitterID', 'twitterPassword', ['http://example.org/feed1.rss', 'http://example.org/feed2.rss'], tag=True)
#instance1.run(debug=True) #Run the first instance, debugging messages on.

# One feed, tag disabled
#instance2 = rss2twitter('ID', 'password', ['http://example.org/feed3.rss'], tag=False)
#instance2.run()

# One feed, custom tag, %s is replaced with the feed title
#instance3 = rss2twitter('ID', 'password', ['http://example.org/feed4.rss'], tag="New from %s")
#instance3.run()
