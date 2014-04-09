import re
from HTMLParser import HTMLParser

class WebPageNode:
    def __init__(self, tag, attrs, parent=None):
        """
        Initialise a WebPageNode object
        """

        self.tag_ = tag
        self.attrs_ = dict(attrs)
        self.parent_ = parent

        self.nodes_ = list()
        self.data_ = None
    
    def get_tags(self):
        return self.tags_
    
    def get_attrs(self):
        return dict(self.attrs_)
    
    def get_data(self):
        return self.data_

    def get_next_child(self, current):
        found = False
        for node in self.nodes_:
            if found:
                return node
            if node == current:
                found = True
        return None
    
    def get_next_children(self, current):
        found = False
        nexts = list()
        for node in self.nodes_:
            if found:
                nexts.append(node)
            if node == current:
                found = True
        return nexts

    def set_data(self, data):
        self.data_ = data

    @staticmethod
    def css_selector_to_query_elts(css_selector_query):
        """
        Convert CSS selector to a list of subqueries
        cf. CSS Selectors: http://www.w3schools.com/cssref/css_selectors.asp

        CSS selectors which are not implemented:
        + :......
        
        For the following CSS selectors, make sure to use space character
        + elt1 + elt2
        + elt1 ~ elt2
        + elt1 > elt2

        eg.: head meta[description]
        eg.: p.myclass
        eg.: a[target=blank_]
        """
        
        if ',' in css_selector_query:
            css_selector_queries = css_selector_query.split(",")
            return [WebPageNode.css_selector_to_query_elts(css) for css in css_selector_queries]
        
        regex_tag = re.compile(r'^([^\.\[\]#]*)')
        regex_id = re.compile(r'#([^\.\[\]#]*)')
        regex_class = re.compile(r'\.([^\.\[\]#]*)')
        regex_attr = re.compile(r'\[([^\.\[\]#=\*~\|\^$]*)([\*~\|\^$]?="([^"]*)"|[\*~\|\^$]?=\'([^\']*)\'|[\*~\|\^$]?=([^\]]+)|)\]') 
        
        query_elts = list()
        query_raw_elts = css_selector_query.split(' ');
        for raw_elt in query_raw_elts:
            if len(raw_elt) == 0:
                continue

            # Tag name
            m = regex_tag.search(raw_elt)
            if m:
                tag = m.group(1)
            else:
                tag = None
            
            # Class & id
            attrs = dict()
            m = regex_id.search(raw_elt)
            if m:
                attrs["id"] = {"value": m.group(1), "type": "="}
            m = regex_class.search(raw_elt)
            if m:
                attrs["class"] = {"value": m.group(1), "type": "="}

            # Attribute
            m = regex_attr.findall(raw_elt)
            for attr_in_query in m:
                # attr_in_query = (attr_name, value with equal and quotations marks, value (if ="value"), value (if ='value'), value (if =value))
                if attr_in_query[1]:
                    if attr_in_query[2]:
                        attrs[attr_in_query[0]] = {"value": attr_in_query[2], "type": attr_in_query[1][0]}
                    elif attr_in_query[3]:
                        attrs[attr_in_query[0]] = {"value": attr_in_query[3], "type": attr_in_query[1][0]}
                    else:
                        attrs[attr_in_query[0]] = {"value": attr_in_query[4], "type": attr_in_query[1][0]}
                else:
                    attrs[attr_in_query[0]] = None
            
            query_elts.append({"tag": tag, "attrs": attrs})
        return query_elts
    
    def is_fit_query(self, query_elt):
        """
        Return True if self fits query_elt
        """
        
        # Tag?
        try:
            if query_elt["tag"] and query_elt["tag"] != "*" and self.tag_ != query_elt["tag"]:
                return False
        except KeyError: # Tag not specified
            pass

        # Other attrs?
        try:
            attrs = query_elt["attrs"]
        except KeyError: # No attrs
            return True

        for name,params in attrs.items():
            # Check if it exists
            try:
                obj_attr = self.attrs_[name]
            except KeyError:
                return False

            # For specific values (if required)
            if not params:
                continue

            if params["type"] == "=": # equals
                if obj_attr != params["value"]:
                    return False
            elif params["type"] == "~": # contains the word
                if not obj_attr.startswith(params["value"]) and not obj_attr.endswith(params["value"]) and " %s " % params["value"] not in obj_attr:
                    return False
            elif params["type"] == "|": # starts with value- or equals value
                if not obj_attr.startswith(params["value"] + "-") and obj_attr != params["value"]:
                    return False
            elif params["type"] == "^": # starts with
                if not obj_attr.startswith(params["value"]):
                    return False
            elif params["type"] == "$": # ends with
                if not obj_attr.endswith(params["value"]):
                    return False
            elif params["type"] == "*": # contains
                if params["value"] not in obj_attr:
                    return False
        
        return True

    def find_(self, query, position_in_query=0):
        """
        Return the WebPageNode(s) that fit the query
        Query is a list of subqueries (usually derived from a CSS selector)
        """
        
        if len(query) <= position_in_query:
            return []
        
        # Skip empty query elements
        if len(query[position_in_query]) == 0:
            return self.find_(query, position_in_query+1)
        
        nodes_with_tag = list()
        
        # Check if we are in a fit-or-fail case
        # when we are starting with a + or ~ we can't afford to wait next node
        fit_or_fail = False
        query_elt = query[position_in_query]
        if query_elt["tag"] == "+" or query_elt["tag"] == "~" or query_elt["tag"] == ">":
            fit_or_fail = True
            position_in_query += 1
            query_elt = query[position_in_query]

            if len(query) <= position_in_query:
                return []
        
        # Does this node fit the requirements for query[position_in_query]?
        fit = self.is_fit_query(query_elt)
        sb_is_fit_or_fail = False
        if fit:
            if len(query) == position_in_query +1:
                nodes_with_tag.append(self)
            elif query[position_in_query +1]["tag"] == "+" or query[position_in_query +1]["tag"] == "~":
                sb_is_fit_or_fail = True
        
        if fit_or_fail:
            if not fit:
                return []
            elif len(query) == position_in_query +1:
                return [self]
        
        # Check remaining elements (sisters and brothers)
        if sb_is_fit_or_fail:
            if query[position_in_query +1]["tag"] == "+":
                sb = self.parent_.get_next_child(self)
                if sb:
                    nodes_with_tag += sb.find_(query, position_in_query+1)
            elif query[position_in_query +1]["tag"] == "~":
                sisters_brothers = self.parent_.get_next_children(self)
                for sb in sisters_brothers:
                    nodes_with_tag += sb.find_(query, position_in_query+1)

        # Check remaining elements (children)
        for node in self.nodes_:
            if fit:
                if len(query) == position_in_query +1 or sb_is_fit_or_fail:
                    nodes_with_tag_n = node.find_(query, position_in_query)
                else:
                    nodes_with_tag_n = node.find_(query, position_in_query+1)
            else:
                nodes_with_tag_n = node.find_(query, position_in_query)
            
            nodes_with_tag += nodes_with_tag_n
        
        return nodes_with_tag
    
    def find(self, query):
        """
        Return the WebPageNode(s) that fit the query
        Query is a string (cf. CSS selector)
        """

        if isinstance(query, list):
            query_elts = query
        else:
            query_elts = WebPageNode.css_selector_to_query_elts(query)

        if len(query_elts) == 0:
            return list()
        
        if isinstance(query_elts[0], list): # we have to deal with an union of queries
            output = list()
            for q in query_elts:
                output = list(set(output + self.find_(q)))
            return output
        else:
            return list(set(self.find_(query_elts)))

    def append_child(self, tag, attrs):
        """
        Append a child to that node
        """
        
        node = WebPageNode(tag, attrs, self)
        self.nodes_.append(node)
        return node

class WebPageParser(HTMLParser):
    def __init__(self):
        self.document_roots = list()
        self.stack_roots = list()

        HTMLParser.__init__(self)
    
    def handle_starttag(self, tag, attrs):
        try:
            # Add this Node to its parent instance
            child = self.stack_roots[-1].append_child(tag, attrs)
        except IndexError:
            # In that case: no parent
            child = WebPageNode(tag, attrs)
            self.document_roots.append(child)
        
        # Add the node to the stack
        self.stack_roots.append(child)

    def handle_endtag(self, tag):
        # Remove the top of the stack
        # The stack has at least one element (because handle_endtag cannot be called before handle_starttag)
        self.stack_roots.pop()

    def handle_data(self, data):
        if len(self.stack_roots) > 0:
            self.stack_roots[-1].set_data(data)

    def find(self, query, source_list=None):
        """
        Return the WebPageNode(s) that fit the query
        """
        
        query_elts = WebPageNode.css_selector_to_query_elts(query)
        
        if not source_list:
            source_list = self.document_roots
        
        result = list()
        for root_node in source_list:
            result += root_node.find(query_elts)
        return result

