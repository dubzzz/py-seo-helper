from seocheck import SEOCheck, SEOCheckNotExist

class SEOCheckManager:
    def __init__(self):
        self.check_list_ = list()
        self.selectors_attrs_ = dict()

    def append(self, seocheck, level=2):
        """
        Append SEOCheck object to the manager
        """

        self.check_list_.append((seocheck, level))

        try:
            self.selectors_attrs_[seocheck.get_css_selector()]
        except KeyError:
            self.selectors_attrs_[seocheck.get_css_selector()] = list()

        if seocheck.get_attr_name() not in self.selectors_attrs_[seocheck.get_css_selector()]:
            self.selectors_attrs_[seocheck.get_css_selector()].append(seocheck.get_attr_name())
    
    def get_check_list(self):
        return self.check_list_

    def get_selectors_attrs(self):
        return self.selectors_attrs_

    def generate_webpage_check_dict(self, webpageparser):
        """
        Return webpage_check_dict
        """
        
        webpage_check_dict = dict()
        for css_selector, attrs in self.selectors_attrs_.items():
            webpage_check_dict[css_selector] = dict()
            corresponding_nodes = webpageparser.find(css_selector)
            for attr in attrs:
                measured_lengths = list()
                if attr: # != None
                    for node in corresponding_nodes:
                        node_attrs = node.get_attrs()
                        try:
                            node_attr = node_attrs[attr]
                        except KeyError:
                            node_attr = None
                        
                        if node_attr:
                            measured_lengths.append(tuple([len(node_attr)]))
                        else:
                            measured_lengths.append(tuple([None]))
                else:
                    for node in corresponding_nodes:
                        if node.get_data():
                            measured_lengths.append(tuple([len(node.get_data())]))
                        else:
                            measured_lengths.append(tuple([None]))
                
                webpage_check_dict[css_selector][attr] = measured_lengths
        
        # SEOCheckNotExist is a special case, it requires the value of the field itself
        # iff regex_specific_value_
        for check_and_level in self.check_list_:
            check = check_and_level[0]
            if isinstance(check, SEOCheckNotExist) and check.regex_specific_value_:
                css_selector = check.get_css_selector()
                attr = check.get_attr_name()
                
                corresponding_nodes = webpageparser.find(css_selector)
                values = list()
                if attr:
                    for node in corresponding_nodes:
                        node_attrs = node.get_attrs()
                        try:
                            node_attr = node_attrs[attr]
                        except KeyError:
                            node_attr = None
                        values.append(node_attr)
                else:
                    for node in corresponding_nodes:
                        if node.get_data():
                            values.append(len(node.get_data()))
                        else:
                            values.append(None)
                
                measured_lengths = webpage_check_dict[css_selector][attr]
                webpage_check_dict[css_selector][attr] = [(measured_lengths[i][0], values[i]) for i in range(len(values))]

        return webpage_check_dict

