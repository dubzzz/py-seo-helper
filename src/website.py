import re
import requests
from webpage import WebPage
from seocheck import SEOCheckExist, SEOCheckNotExist, SEOCheckLength, SEOCheckLengthBetween
from seocheckmanager import SEOCheckManager
from outputprinter import StandardPrinter
from test import Test

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
        # HTML
        self.seocheckmanager.append(SEOCheckExist("html", "lang", "Missing LANG attribute for <HTML/>", "Setting this value can help you to get a better ranking based on the localization of the user who is using a search engine and the subdomain in use for this search engine. Results and positioning in google.com and google.co.uk are not the same"), 2)
        # HEAD / LINK
        self.seocheckmanager.append(SEOCheckExist("html > head > link[rel~=icon]", "href", "Missing FAVICON"), 3)
        # HEAD / TITLE
        self.seocheckmanager.append(SEOCheckExist("html > head > title", None, "Missing <TITLE/>"), 0)
        self.seocheckmanager.append(SEOCheckLength("html > head > title", None, ">", 70, "Too long <TITLE/>"), 1)
        # HEAD / META[description]
        self.seocheckmanager.append(SEOCheckExist("html > head > meta[name=description]", "content", "Missing META for description"), 0)
        self.seocheckmanager.append(SEOCheckLength("html > head > meta[name=description]", "content", "<", 50, "Too short META for description"), 1)
        self.seocheckmanager.append(SEOCheckLength("html > head > meta[name=description]", "content", ">", 160, "Too long META for description"), 1)
        self.seocheckmanager.append(SEOCheckLengthBetween("html > head > meta[name=description]", "content", 150, 160, "Recommended META for description: between 150 and 160"), 3)
        # HEAD / META[robots]
        self.seocheckmanager.append(SEOCheckExist("html > head > meta[name=robots]", "content", "Missing META for robots"), 1)
        # H1
        self.seocheckmanager.append(SEOCheckExist("h1", None, "Missing <H1/>"), 0)
        # IMG
        self.seocheckmanager.append(SEOCheckNotExist("img", "src", "(.+)", "Missing SRC attribute for <IMG/>", "src attribute should be specified on every <img/>"), 0)
        self.seocheckmanager.append(SEOCheckNotExist("img", "alt", "(.+)", "Missing ALT attribute for <IMG/>"), 0)
        self.seocheckmanager.append(SEOCheckLength("img", "alt", ">", 80, "Too long ALT attribute for <IMG/>"), 2)
        # A
        self.seocheckmanager.append(SEOCheckNotExist("a", "href", "(.+)", "Missing HREF attribute for <A/>", "<a/> links are used to create hyperlinks. href should be specified on every <a/> link"), 0)
        self.seocheckmanager.append(SEOCheckNotExist("a[href^='/'] , a[href^='%s']" % self.root_url, None, "(.+)", "Missing visible/anchor text of <A/> (internal link)", "Anchor text of <a/> links is useful because it helps bots to understand what kind of page is targetted. It gives bots keywords that could be attributed to the webpage"), 2)
        self.seocheckmanager.append(SEOCheckNotExist("a[href='#']", None, None, "Use of <a href='#' />", "For my part, I prefer using <a href='javascript:void(0);' onclick='...' /> instead of <a href='#' onclick='...' />. <a href='#' /> makes the page scrolling up when clicked"), 3)
        # APPLET / IFRAME
        self.seocheckmanager.append(SEOCheckNotExist("applet", "code", "(.+)", "Missing CODE attribute for <APPLET/>"), 3)
        self.seocheckmanager.append(SEOCheckNotExist("iframe", "src", "(.+)", "Missing SRC attribute for <IFRAME/>"), 3)
        # I / B
        self.seocheckmanager.append(SEOCheckNotExist("i , b", "class", "(^| )(glyphicon)($| )", "Recommended: use <strong/> and <em/> instead of <i/> and <b/>"), 2)
    
    def append(self, webpage):
        """
        Append a webpage to the list of currently in use WebPages

        /!\ Does not check if the page is already in the list
        """
        
        webpage.id = len(self.webpages)
        self.webpages.append(webpage)
        self.url_to_id[webpage.url] = webpage.id

        return webpage.id

    def retrieve_webpage(self, from_wp, url, as_ressource=False):
        """
        Return the corresponding WebPage object
        Create it if it was not defined before
        """
        
        extended = False
        if url.startswith('//'):
            url = "http:" + url
        elif url.startswith('/'):
            url = self.root_url + url[1:]
            extended = True
        elif not url.startswith("http"):
            without_slashes = from_wp.url.split('?')[0].split('/')
            url = '/'.join(without_slashes[:-1]) + '/' + url

        try:
            wp_id = self.url_to_id[url]
        except KeyError:
            wp = WebPage(url, from_wp.depth +1, extended | url.startswith(self.root_url))
            wp_id = self.append(wp)
        
        wp = self.webpages[wp_id]
        if as_ressource:
            wp.add_ressource_used_by(from_wp)
        else:
            wp.add_link_used_by(from_wp)
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
        
        # TEST
        tests = list()

        # Robots.txt / Sitemaps
        
        t_robots = Test("Missing robots.txt", "'robots.txt' file tells search engines whether they can access and therefore crawl parts of your site", 0)
        
        error_robots = False
        try:
            robots_webpage = requests.get(self.root_url + "robots.txt", timeout=10)
        except requests.ConnectionError:
            error_robots = True
        except requests.exceptions.Timeout:
            error_robots = True
        except requests.exceptions.InvalidSchema:
            error_robots = True
        if error_robots or robots_webpage.status_code != 200:
            t_robots.set_passed(False)

        tests.append(t_robots)

        # Broken links check
        # Good balance between internal/external links

        t_brokenlinks = Test("Broken links", "Broken links affects your ranking", 0)
        t_brokenlinks_in = Test("Broken links in", "Broken links have been detected in the following webpages", 0)
        t_brokenressources_in = Test("Broken ressources in", "Broken ressources (image source, js script, css stylesheets) have been detected in the following webpages", 0)
        t_duplicated_title = Test("Duplicated Title (on pages to be indexed)", "Webpages with identical titles are very harmful for the ranking", 1)
        t_duplicated_description = Test("Duplicated Description (on pages to be indexed)", "Webpages with identical descriptions are very harmul for the ranking", 1)
        t_internal_external_links = Test("Too many external links", "Some people believe that the number of external links should be inferior to the number of internal links. Choose your links properly in order to avoid becoming a directory for websites. You can also use rel='nofollow' attribute in order do remove their effects on your ranking", 3)

        for webpage in self.webpages:
            if webpage.status not in (200, 301, 302):
                t_brokenlinks.append(webpage)
            if webpage.has_brokenlinks:
                t_brokenlinks_in.append(webpage)
            if webpage.has_brokenressources:
                t_brokenressources_in.append(webpage)
            if webpage.duplicated_title:
                t_duplicated_title.append(webpage)
            if webpage.duplicated_description:
                t_duplicated_description.append(webpage)
            if webpage.link_towards_ext and webpage.link_towards_int and len(webpage.link_towards_ext) > len(webpage.link_towards_int):
                t_internal_external_links.append(webpage)

        tests.append(t_brokenlinks)
        tests.append(t_brokenlinks_in)
        tests.append(t_brokenressources_in)
        tests.append(t_duplicated_title)
        tests.append(t_duplicated_description)
        tests.append(t_internal_external_links)

        # SEOCheck - local checks

        seochecks_and_levels = self.seocheckmanager.get_check_list()
        for check_and_level in seochecks_and_levels:
            check = check_and_level[0]
            level = check_and_level[1]

            t_check = Test(check.get_title(), check.get_description(), level)
            for webpage in self.webpages:
                check_dict = webpage.get_check_dict()
                if not check_dict:
                    continue
                if not check.check(check_dict):
                    t_check.append(webpage)
            tests.append(t_check)

        # Display results

        failed_tests = list()
        passed_tests = list()

        for t in tests:
            if t.get_passed():
                passed_tests.append(t)
            else:
                failed_tests.append(t)
        
        print ""
        sprinter = StandardPrinter()
        sprinter.render(self.webpages, failed_tests, passed_tests)

