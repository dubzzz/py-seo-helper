#!/usr/bin/python

import sys
import getopt
from website import WebSite

help_content = """SEO Helper - https://github.com/dubzzz/py-seo-helper

NAME
    scan - SEO Tool that evaluates which points can be improved in order to get a better positioning
    
SYNOPSIS
    ./scan.py -u [url]

DESCRIPTION
    -h, --help
        Display help.

    -u [url], --url=[url]
        URL where the analysis will start. The crawler will then crawl from page to page.
        The URL must end by /.

    -d [max-depth], --max-depth=[max-depth]
        Specify a different value for max-depth. By default: max-depth=5.

    --nofollow
        By default, the crawler follows every link in the page. By using this option, the crawler will not follow links tagged with rel='nofollow'.

    --noindex
        By default, the output includes every page of your website that can be reached in max-depths clicks.
        By using --noindex option results with <meta name='robots' content='noindex' /> will not be diplayed
    
    -m [me@domain.com], --email=[me@domain.com]
        Specify the email address of the user that should received the PDF report. Not specified implies no email, but PDF generation in ./output/pdf.pdf.

    -a, --deep
        Deep analysis. Instead of asking only for the header of external webpages (default behaviour), it will ask the complete webpage.
        This kind of analysis will certainly be a bit longer. It allows to follow redirections and check whether or not the targetted element is accessible.

    -c, --color
        Colored output. Default: no-colors.
"""

try:
    opts, args = getopt.getopt(sys.argv[1:], "dum:hca", ["max-depth=", "url=", "help", "nofollow", "noindex", "email=", "color", "deep"])
except getopt.GetoptError as err:
    print help_content
    print(str(err))
    sys.exit(0x0001)

url = None
max_depth = 5
nofollow = False
noindex = False
email_address = None
color = False
deep = False

for opt, arg in opts:
    if opt in ("-h", "--help"):
        print help_content
        sys.exit(0)
    elif opt in ("-u", "--url"):
        url = arg
    elif opt in ("-d", "--max-depth"):
        try:
            max_depth = int(arg)
        except ValueError:
            print "INVALID PARAMETER for max-depth: MUST BE an INTEGER\n"
            print help_content
            sys.exit(1)
        except TypeError:
            print "INVALID PARAMETER for max-depth: MUST BE an INTEGER\n"
            print help_content
            sys.exit(1)
    elif opt in ("--nofollow"):
        nofollow = True
    elif opt in ("--noindex"):
        noindex = True
    elif opt in ("-e", "--email"):
        email_address = arg
    elif opt in ("-c", "--color"):
        color = True
    elif opt in ("-a", "--deep"):
        deep = True

if not url:
    print "MISSING PARAMETER: url\n"
    print help_content
    sys.exit(1)

del help_content

website = WebSite(url)
website.scan(max_depth, email_address, nofollow, noindex, deep, color)

