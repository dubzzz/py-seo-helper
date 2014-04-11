import os
import cgi
import subprocess
from abc import abstractmethod, ABCMeta

class OutputPrinter:
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def render(self, webpages, failed_tests, passed_tests):
        pass

class StandardPrinter(OutputPrinter):
    def __init__(self, color=False):
        OutputPrinter.__init__(self)
        self.color_ = color
    
    def render(self, webpages, failed_tests, passed_tests):
        print "WEBPAGES TESTED:\n"
        for wp in webpages:
            content_type = wp.content_type
            if not content_type:
                content_type = ""
            if not self.color_:
                print "[%d] %s - %s - %s" % (wp.status, wp.url, wp.get_formatted_length(), content_type)
            elif wp.status == 200:
                print "[\033[92m%d\033[0m] %s - %s - %s" % (wp.status, wp.url, wp.get_formatted_length(), content_type)
            elif wp.status >= 300 and wp.status < 400:
                print "[\033[93m%d\033[0m] %s - %s - %s" % (wp.status, wp.url, wp.get_formatted_length(), content_type)
            elif wp.status >= 400:
                print "[\033[91m%d\033[0m] %s - %s - %s" % (wp.status, wp.url, wp.get_formatted_length(), content_type)
            else:
                print "[%d] %s - %s - %s" % (wp.status, wp.url, wp.get_formatted_length(), content_type)
        
        print "\nFAILED TESTS:\n"
        for test in failed_tests:
            print "\nName:     ", test.get_title()
            if not self.color_ or test.get_level() < 0 or test.get_level() >= 4:
                print "Severity: ", test.get_level_str()
            elif test.get_level() == 0:
                print "Severity: \033[91m", test.get_level_str(), "\033[0m"
            elif test.get_level() == 1:
                print "Severity: \033[93m", test.get_level_str(), "\033[0m"
            elif test.get_level() == 2:
                print "Severity: \033[94m", test.get_level_str(), "\033[0m"
            elif test.get_level() == 3:
                print "Severity: \033[92m", test.get_level_str(), "\033[0m"
            print "Details:  ", test.get_description()
            print ""
            for wp in test.get_failures():
                print "+ ", wp.url

        print "\nPASSED TESTS:"
        for test in passed_tests:
            print "+ ", test.get_title()

class PDFPrinter(OutputPrinter):
    def __init__(self, root_url, filename, email_address=None):
        OutputPrinter.__init__(self)
        self.root_url_ = root_url
        self.filename_ = filename
        self.email_address_ = email_address

    def render(self, webpages, failed_tests, passed_tests):
        SRC_PATH = os.path.dirname(os.path.abspath(__file__))
        BIN_PATH = os.path.join(SRC_PATH, "../bin/")
        OUT_PATH = os.path.join(SRC_PATH, "../output/")
        
        HTML_PATH = os.path.join(OUT_PATH, "output.html")
        WK_PATH = os.path.join(BIN_PATH, "wkhtmltopdf")
        PDF_PATH = os.path.join(OUT_PATH, self.filename_)
        with open(HTML_PATH, "w+") as f:
            f.write('<!DOCTYPE html>')
            f.write('<html><head>')
            f.write("<link href='main.css' rel='stylesheet' type='text/css' />")
            f.write('</head><body>')

            f.write('<div class="pages">')
            
            f.write('<div class="page">')
            f.write('<h1>SEO Helper</h1>')
            f.write('<p class="links"><a href="%s">%s</a><br/><a href="https://github.com/dubzzz/py-seo-helper">GitHub of the project</a></p>' % (self.root_url_, self.root_url_))
            f.write('</div>')

            f.write('<div class="page">')
            f.write('<h2>Scanned pages:</h2><ul>')
            for wp in webpages:
                content_type = wp.content_type
                if not content_type:
                    content_type = ""
                f.write('<li><p>%s</p>' % cgi.escape(wp.url))
                f.write('<p class="details">')
                f.write('<span class="status">Status: <span data-value="%d">%d</span></span>' % (wp.status, wp.status))
                f.write('<span class="depth">#clicks: <span data-value="%d">%d</span></span>' % (wp.depth, wp.depth))
                f.write('<span class="content-type">Content-type: <span data-value="%s">%s</span></span>' % (cgi.escape(content_type, quote=True), cgi.escape(content_type)))
                f.write('<span class="length">Length: <span data-value="%s">%s</span></span>' % (cgi.escape(wp.get_formatted_length(), quote=True), cgi.escape(wp.get_formatted_length())))
                f.write('</p></li>')
            f.write('</ul>')
            f.write('</div>')

            f.write('<div class="page">')
            f.write('<h2>Improvements:</h2>')
            for test in failed_tests:
                f.write('<h3><span class="severity">[<span class="level%d">%s</span>]</span> %s</h3>' % (test.get_level(), cgi.escape(test.get_level_str()), cgi.escape(test.get_title())))
                f.write('<p class="description">%s</p>' % cgi.escape(test.get_description()))
                f.write('<ul>')
                for wp in test.get_failures():
                    f.write('<li>%s</li>' % cgi.escape(wp.url))
                f.write('</ul>')
            f.write('</div>')
            
            f.write('<div class="page">')
            f.write('<h2>Passed tests:</h2><ul>')
            for test in passed_tests:
                f.write('<li><span class="severity">[<span class="level%d">%s</span>]</span> %s</li>' % (test.get_level(), cgi.escape(test.get_level_str()), cgi.escape(test.get_title())))
            f.write('</ul>')
            f.write('</div>')
            
            f.write('</div>')

            f.write('</body></html>')
        
        sp_wk = subprocess.Popen([WK_PATH, "--page-size", "A4", "--margin-left", "10mm", "--margin-right", "10mm", "--margin-top", "10mm", "--margin-bottom", "10mm", HTML_PATH, PDF_PATH])
        sp_wk.wait()

        if self.email_address_:
            sp_echo = subprocess.Popen(["echo", "Please find attach the output"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            sp_mutt = subprocess.Popen(["mutt", "-s", "SEO Helper - output", "-a", PDF_PATH, "--", self.email_address_], stdin=sp_echo.stdout, stdout=subprocess.PIPE)
            sp_echo.stdout.close()
            sp_mutt.wait()

