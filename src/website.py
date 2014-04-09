import re
from webpage import WebPage
from seocheck import SEOCheckExist, SEOCheckNotExist, SEOCheckLength, SEOCheckLengthBetween
from seocheckmanager import SEOCheckManager

class WebSite:
    
    def __init__(self, start_url):
        """
        Initialise an instance of WebSite
        """
        
        self.start_url = start_url
        
        m = re.match(r'^(http[s]?://[a-zA-Z0-9\.-]+/)', self.start_url)
        if not m:
            raise ValueError("'start_url' must be an URL starting by http:// or https://")
        self.root_url = m.group(0) # has / at the end

        self.seocheckmanager = SEOCheckManager()
        self.seocheckmanager.append(SEOCheckExist("html > head > meta[name=description]", "content", "Missing META for description"))
        self.seocheckmanager.append(SEOCheckLength("html > head > meta[name=description]", "content", "<", 50, "Too short META for description"))
        self.seocheckmanager.append(SEOCheckLength("html > head > meta[name=description]", "content", ">", 160, "Too long META for description"))
        #self.seocheckmanager.append(SEOCheckLengthBetween("html > head > meta[name=description]", "content", 150, 160, "Recommended META for description: between 150 and 160"))
        self.seocheckmanager.append(SEOCheckNotExist("i , b", "class", "(^| )(glyphicon)($| )", "Recommended: use <strong/> and <em/> instead of <i/> and <b/>"))
    
    def append(self, webpage):
        """
        Append a webpage to the list of currently in use WebPages

        /!\ Does not check if the page is already in the list
        """
        
        webpage.id = len(self.webpages)
        self.webpages.append(webpage)
        self.url_to_id[webpage.url] = webpage.id

        return webpage.id

    def retrieve_webpage(self, from_wp, url):
        """
        Return the corresponding WebPage object
        Create it if it was not defined before
        """
        
        if url.startswith('/'):
            url = self.root_url + url[1:]
            extended = True
        else:
            extended = False

        try:
            wp_id = self.url_to_id[url]
        except KeyError:
            wp = WebPage(url, from_wp.depth +1, extended | url.startswith(self.root_url))
            wp_id = self.append(wp)
        
        wp = self.webpages[wp_id]
        wp.add_link_from(from_wp)
        return wp
    
    def scan(self, max_depth):
        """
        Scan the WebSite in order to report abnormal or non-optimal
        coding choices
        """
        
        # webpages contains the list of known pages
        # pages that have been or should be seen during scan
        # for max_depth=+infinity
        self.webpages = list()
        
        # faster lookup
        self.url_to_id = dict()
        
        self.append(WebPage(self.start_url))
        
        # BFS parameters
        cursor_webpages_pos = 0
        
        # while we do not reach the maximal allowed depth or visit everything
        while cursor_webpages_pos < len(self.webpages) and self.webpages[cursor_webpages_pos].depth <= max_depth:
            # remove and return the head of the queue
            webpage = self.webpages[cursor_webpages_pos]
            webpage.scan(self, self.seocheckmanager)
            
            cursor_webpages_pos += 1
        
        # TODO Robots.txt / Sitemaps
        # TODO Deadlinks check
        # SEOCheck - local checks
        seochecks = self.seocheckmanager.get_check_list()
        for check in seochecks:
            print check.get_label()
            for webpage in self.webpages:
                check_dict = webpage.get_check_dict()
                if not check_dict:
                    continue
                if not check.check(check_dict):
                    print "+ ", webpage.get_url()

