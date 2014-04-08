import requests
import re

class WebPage:
    def __init__(self, url, depth=0, internal=True):
        """
        Initialise an instance of WebPage
        """
        
        self.id = None
        self.url = url
        self.depth = depth
        self.internal = internal

        self.link_from = list()
        self.link_towards_ext = None # None => not analysed
        self.link_towards_int = None

        self.server_unreachable = False
        self.status = None
        self.content_type = None
        self.content_length = None
    
    def add_link_from(self, from_wp):
        """
        A scanned webpage has a link towards this page
        """

        self.link_from.append(from_wp)

    def scan(self, website):
        """
        Scan the webpage
        looking for relationships with other pages
        """
        
        self.link_towards_ext = list()
        self.link_towards_int = list()

        try:
            webpage_head = requests.head(self.url, timeout=10)
        except requests.ConnectionError:
            self.server_unreachable = True
        except requests.exceptions.Timeout:
            self.server_unreachable = True
        
        # 200: OK
        # 301: moved permanently
        self.status = webpage_head.status_code
        if webpage_head.headers['content-type']:
            m = re.match(r'[a-zA-Z\.0-9-]+/[a-zA-Z\.0-9-]+', webpage_head.headers['content-type'])
            if m:
                self.content_type = m.group(0)
        try:
            self.content_length = int(webpage_head.headers['content-length'])
        except TypeError:
            pass
        except ValueError:
            pass
        print "depth=%d, url=%s [%s][%d]" % (self.depth, self.url, self.content_type, self.status)
        
        # Not a success
        # or external page
        if self.status != 200 or not self.internal or "text/html" not in self.content_type:
            return
        
        try:
            webpage_query = requests.get(self.url, timeout=10)
        except requests.ConnectionError:
            self.server_unreachable = True
        except requests.exceptions.Timeout:
            self.server_unreachable = True
        
        # Status can change when we run a get query
        # eg. 500 status can be caused by a programming error that cancels the generation of the page
        self.status = webpage_query.status_code
        if self.status != 200:
            return
        
        # The best way to get the real value of content-length is to compute it from the data
        # The value returned by a server during head/get query for non-static files is not good (except on custom configurations of Apache)
        self.content_length = len(webpage_query.text)
        
        # Analyse the source code of the webpage
        # Look for other pages
        links = re.findall(r'<a[^>]+href="(?P<url>(?:http[s]?://|/)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)"[^>]*>', webpage_query.text)
        for link in links:
            wp = website.retrieve_webpage(self, link)
            if wp.internal:
                self.link_towards_int.append(wp)
            else:
                self.link_towards_ext.append(wp)

