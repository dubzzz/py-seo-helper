from HTMLParser import HTMLParser
from collections import defaultdict

class WebPageNode:
    def __init__(self, attrs=list()):
        """
        Initialise a WebPageNode object
        """

        self.nodes = defaultdict(list)
        self.data = None
        self.attrs = attrs
    
    def get_attrs(self):
        return dict(self.attrs)

    def set_data(self, data):
        self.data = data

    def find_firsts_with_tag(self, tag_name):
        """
        Return the WebPageNode(s) that have tag_name
        """
        
        if not self.nodes:
            return list()

        with_tag = list()
        for key, nodes in self.nodes.iteritems():
            if key == tag_name:
                with_tag += nodes
            else:
                for n in nodes:
                    with_tag_n = n.find_firsts_with_tag(tag_name)
                    if len(with_tag_n) > 0:
                        with_tag += with_tag_n

        return with_tag

    def append_child(self, tag, attrs):
        """
        Append a child to that node
        """
        
        node = WebPageNode(attrs)
        self.nodes[tag].append(node)
        return node

class WebPageParser(HTMLParser):
    def __init__(self):
        self.document_root = WebPageNode()
        
        self.last_root = self.document_root
        self.stack_roots = list()
        self.stack_roots.append(self.document_root)

        HTMLParser.__init__(self)
    
    def handle_starttag(self, tag, attrs):
        child = self.last_root.append_child(tag, attrs)
        self.stack_roots.append(child)
        self.last_root = child

    def handle_endtag(self, tag):
        self.last_root = self.stack_roots.pop()

    def handle_data(self, data):
        self.last_root.set_data(data)

    def find_firsts_with_tag(self, tag_name):
        """
        Return the WebPageNode(s) that have tag_name
        
        Will not return p#second for tag_name="p" and <p id="first"><p id="second"></p></p>
        Return only the firsts p nodes (not their children)
        """

        return self.document_root.find_firsts_with_tag(tag_name)

