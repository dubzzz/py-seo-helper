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
    
    def carryout_request(self, full_request, num_retry=0):
        """
        Try to get the webpage content/header of self.url

        full_request  : content
        ! full_request: header

        It will retry num_retry times before stopping. The maximum number of tries is num_retry +1
        """
        
        retry = 0
        webpage = None
        
        while retry <= num_retry and not webpage:
            retry += 1
            print "Try #%d: %s" % (retry, self.url)
            self.server_unreachable = False
            self.server_invalid_query = False
            try:
                if full_request:
                    webpage = requests.get(self.url, timeout=10)
                else:
                    webpage = requests.head(self.url, timeout=10)
            except requests.ConnectionError:
                self.server_unreachable = True
                wbepage = None
            except requests.exceptions.Timeout:
                self.server_unreachable = True
                webpage = None
            except requests.HTTPError:
                self.server_invalid_query = True
                webpage = False
            except requests.exceptions.TooManyRedirects:
                self.server_invalid_query = True
                return None
            except requests.exceptions.InvalidSchema:
                self.server_invalid_query = True
                return None

        if not webpage:
            return None
        
        # Status
        self.status = webpage.status_code
        
        # Content-type
        try:
            if webpage.headers['content-type']:
                m = re.search(r'[a-zA-Z\.0-9-]+/[a-zA-Z\.0-9-]+', webpage.headers['content-type'])
                if m:
                    self.content_type = m.group(0)
        except KeyError:
            pass

        # Content-length
        # The best way to get the real value of content-length is to compute it from the data
        # The value returned by a server during head/get query for non-static files is not good (except on custom configurations of Apache)
        if full_request:
            self.content_length = len(webpage.text)
        else:
            try:
                self.content_length = int(webpage.headers['content-length'])
            except TypeError:
                pass
            except ValueError:
                pass
            except KeyError:
                   pass

        return webpage
    
    def sourcecode_analysis(self, html_code, website, seocheckmanager, nofollow, noindex):
        """
        Analyse the source code of the webpage
        in order to give relevant details concerning ways to improve the ranking of the website

        This analysis focus on:
        + Gathering data for SEOChecks
        + Adding probes in order to check the availability of ressources (images, favicons, iframes, applets, stylesheets or js scripts)
        + Adding probes to crawl pages that are directly linked to this one
        + Getting title and description to find possible duplicates beween different pages
        """
        
        webpageparser = WebPageParser()
        webpageparser.feed(html_code)
        
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

    @check_failures
    def scan(self, website, seocheckmanager, noindex, nofollow, deep, num_retry):
        """
        Scan the webpage
        looking for relationships with other pages
        """
        
        self.link_towards_ext = list()
        self.link_towards_int = list()
        self.ressource_from = list()
        
        webpage_header = self.carryout_request(False, num_retry)
        if not webpage_header:
            return

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
        
        self.status = 0
        self.content_length = None
        webpage_query = self.carryout_request(True, num_retry)
        if not webpage_query:
            return
        
        # Status can change when we run a get query
        # eg. 500 status can be caused by a programming error that cancels the generation of the page
        if self.status != 200:
            return
        
        # Stop there for external webpages and deep analysis
        if not self.internal:
            return

        self.sourcecode_analysis(webpage_query.text, website, seocheckmanager, nofollow, noindex)
        return

    def get_check_dict(self):
        return self.check_dict

