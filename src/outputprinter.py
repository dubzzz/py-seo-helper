from abc import abstractmethod, ABCMeta

class OutputPrinter:
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def render(self, webpages, failed_tests, passed_tests):
        pass

class StandardPrinter(OutputPrinter):
    def render(self, webpages, failed_tests, passed_tests):
        print "WEBPAGES TESTED:\n"
        for wp in webpages:
            content_type = wp.content_type
            if not content_type:
                content_type = ""
            print "[%d] %s - %s - %s" % (wp.status, wp.url, wp.get_formatted_length(), content_type)
        
        print "\nFAILED TESTS:\n"
        for test in failed_tests:
            print "\nName:     ", test.get_title()
            print "Severity: ", test.get_level_str()
            print "Details:  ", test.get_description()
            print ""
            for wp in test.get_failures():
                print "+ ", wp.url

        print "\nPASSED TESTS:"
        for test in passed_tests:
            print "+ ", test.get_title()

