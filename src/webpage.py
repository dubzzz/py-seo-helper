import requests
import re
from hashlib import sha512
from webpageparser import WebPageParser, WebPageNode

class WebPage:
    titles_seen = dict()
    descriptions_seen = dict() # hash for description: id of the first webpage

    regex_url = re.compile(r'(?:http[s]?:/|)/(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    
    def __init__(self, url, depth=0, internal=True):
        """
        Initialise an instance of WebPage
        """
        
        self.id = None
        self.url = url
        self.depth = depth
        self.internal = internal
        self.noindex = False

        self.link_used_by = list()
        self.ressource_used_by = list()

        self.link_towards_ext = None # None => not analysed
        self.link_towards_int = None
        self.ressource_from = None
        
        self.has_brokenlinks = False
        self.has_brokenressources = False

        self.server_unreachable = False
        self.server_invalid_query = False
        self.status = 0
        self.content_type = None
        self.content_length = None
        
        self.duplicated_title = False
        self.duplicated_description = False
        self.check_dict = None
    
    def get_url(self):
        return self.url

    def get_formatted_length(self):
        if not self.content_length:
            return "N.A."
        
        unit = 0
        length = self.content_length
        while length >= 1024:
            unit += 1
            length /= 1024.

        units = ["o", "ko", "Mo", "Go", "To"]
        if unit >= len(units):
            return "N.A."
        if unit == 0:
            return "%d%s" % (int(length), units[unit])
        return "%d.%d%s" % (int(length), int((length*10.)%10), units[unit])

    def add_link_used_by(self, from_wp):
        """
        A scanned webpage has a link towards this page
        """

        self.link_used_by.append(from_wp)

    def add_ressource_used_by(self, from_wp):
        """
        A scanned webpage uses this webpage as a resource
        """

        self.ressource_used_by.append(from_wp)
    
    def check_failures(func):
        def inner(*args, **kwargs):
            output = func(*args, **kwargs)
            
            self = args[0]
            print "depth=%d, url=%s [%s][%d]" % (self.depth, self.url, self.content_type, self.status)
            
            if self.status not in (200, 301, 302):
                for wp in self.link_used_by:
                    wp.has_brokenlinks = True
                for wp in self.ressource_used_by:
                    wp.has_brokenressources = True
            return output
        return inner

    @check_failures
    def scan(self, website, seocheckmanager, noindex, nofollow, deep):
        """
        Scan the webpage
        looking for relationships with other pages
        """
        
        self.link_towards_ext = list()
        self.link_towards_int = list()
        self.ressource_from = list()
        
        try:
            webpage_head = requests.head(self.url, timeout=10)
        except requests.ConnectionError:
            self.server_unreachable = True
            return
        except requests.exceptions.Timeout:
            self.server_unreachable = True
            return
        except requests.exceptions.InvalidSchema:
            self.server_invalid_query = True
            return
         
        # 200: OK
        # 301: moved permanently
        self.status = webpage_head.status_code
        if webpage_head.headers['content-type']:
            m = re.search(r'[a-zA-Z\.0-9-]+/[a-zA-Z\.0-9-]+', webpage_head.headers['content-type'])
            if m:
                self.content_type = m.group(0)
        try:
            self.content_length = int(webpage_head.headers['content-length'])
        except TypeError:
            pass
        except ValueError:
            pass
        
        # Not a success
        # or external page
        if deep:
            if not self.content_type: # if content-type is not defined for deep analysis: full request
                pass
            elif self.status not in (200, 301, 302) or "text/html" not in self.content_type:
                return
        else:
            if self.status != 200 or not self.internal or not self.content_type or "text/html" not in self.content_type:
                return
        
        try:
            self.status = 0
            self.content_length = None
            webpage_query = requests.get(self.url, timeout=10)
        except requests.ConnectionError:
            self.server_unreachable = True
            return
        except requests.exceptions.Timeout:
            self.server_unreachable = True
            return
        except requests.exceptions.InvalidSchema:
            self.server_invalid_query = True
            return
        
        if not self.content_type:
            if webpage_query.headers['content-type']:
                m = re.search(r'[a-zA-Z\.0-9-]+/[a-zA-Z\.0-9-]+', webpage_query.headers['content-type'])
                if m:
                    self.content_type = m.group(0)

        # Status can change when we run a get query
        # eg. 500 status can be caused by a programming error that cancels the generation of the page
        self.status = webpage_query.status_code
        if self.status != 200:
            return
        
        # The best way to get the real value of content-length is to compute it from the data
        # The value returned by a server during head/get query for non-static files is not good (except on custom configurations of Apache)
        self.content_length = len(webpage_query.text)
        
        # Stop there for external webpages and deep analysis
        if not self.internal:
            return

        # Analyse the source code of the webpage
        
        webpageparser = WebPageParser()
        webpageparser.feed(webpage_query.text)
        
        # SEOCheckManager
        self.check_dict = seocheckmanager.generate_webpage_check_dict(webpageparser)
        
        # Look for ressources
        nodes_ressources = webpageparser.find("script[src] , link[href] , img[src] , iframe[src] , object[data] , applet[code]")
        for node in nodes_ressources:
            try:
                node_tag = node.get_tag()
                node_attrs = node.get_attrs()
                
                if node_tag == "link":
                    url = node_attrs["href"]
                elif node_tag == "object":
                    url = node_attrs["data"]
                elif node_tag == "applet":
                    url = node_attrs["code"]
                else:
                    url = node_attrs["src"]
                m_url = WebPage.regex_url.match(url)
                if m_url:
                    wp = website.retrieve_webpage(self, url, True)
                    self.ressource_from.append(wp)
                    if wp.status and wp.status not in (200, 301, 302):
                        self.has_brokenressources = True
            except KeyError:
                pass
        
        # meta[name=robots]
        nofollow_global = False
        if nofollow:
            nodes = webpageparser.find("meta[name=robots][content*=nofollow]")
            if len(nodes) >= 1:
                nofollow_global = True
        
        # Look for other pages
        if not nofollow_global:
            nodes_a = webpageparser.find("a[href]")
            for node in nodes_a:
                try:
                    node_attrs = node.get_attrs()
                    
                    url = node_attrs["href"]
                    try:
                        nofollow_local = "nofollow" in node_attrs["rel"]
                    except KeyError:
                        nofollow_local = False

                    if nofollow and nofollow_local:
                        continue

                    m_url = WebPage.regex_url.match(url)
                    if m_url:
                        wp = website.retrieve_webpage(self, url)
                        if wp.internal:
                            self.link_towards_int.append(wp)
                        else:
                            self.link_towards_ext.append(wp)
                        if wp.status and wp.status not in (200, 301, 302):
                            self.has_brokenlinks = True
                except KeyError:
                    pass
        
        # title / description
        nodes = webpageparser.find("head > meta[name=robots][content*=noindex]")
        if len(nodes) >= 1:
            self.noindex = True
            
            if noindex:
                return

        nodes = webpageparser.find("head > title")
        if len(nodes) >= 1:
            node = nodes[0]
            title = node.get_data()
            if title:
                title_digest = sha512(title.encode('utf-8')).digest()
                if title_digest in WebPage.titles_seen.keys():
                    self.duplicated_title = True
                    WebPage.titles_seen[title_digest].duplicated_title = True
                else:
                    WebPage.titles_seen[title_digest] = self

        nodes = webpageparser.find("head > meta[name=description][content]")
        if len(nodes) >= 1:
            node = nodes[0]
            description = node.get_attrs()["content"]
            if description:
                description_digest = sha512(description.encode('utf-8')).digest()
                if description_digest in WebPage.descriptions_seen.keys():
                    self.duplicated_description = True
                    WebPage.descriptions_seen[description_digest].duplicated_description = True
                else:
                    WebPage.descriptions_seen[description_digest] = self
        

    def get_check_dict(self):
        return self.check_dict

