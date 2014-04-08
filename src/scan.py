#!/usr/bin/python

import sys
from website import WebSite

if len(sys.argv) < 2 or len(sys.argv) > 3:
    print "SYNTAX: ./scan.py [website's url] ([max_depth=5])"
else:
    start_url = sys.argv[1]
    try:
        max_depth = sys.argv[2]
    except IndexError:
        max_depth = 5
    
    website = WebSite(start_url)
    website.scan(max_depth)

