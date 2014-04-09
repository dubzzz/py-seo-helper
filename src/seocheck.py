import re
from abc import abstractmethod

class SEOCheck:
    def __init__(self, css_selector, attr_name, label=None, description=None):
        """
        Constructor for SEOCheck
        
        eg. css_selector: "p > a.link"
        eg. attr_name: None => data
        """
        
        self.css_selector_ = css_selector
        self.attr_name_ = attr_name

        self.label_ = label
        self.description_ = description
    
    def get_css_selector(self):
        return self.css_selector_
    
    def get_attr_name(self):
        return self.attr_name_
    
    def get_label(self):
        return self.label_

    def get_description(self):
        return self.description_

    @abstractmethod
    def check_unitary(self, webpage_check_dict_elt):
        pass

    def check(self, webpage_check_dict):
        for elt in webpage_check_dict[self.css_selector_][self.attr_name_]:
            if not self.check_unitary(elt):
                return False
        return True

class SEOCheckExist(SEOCheck):
    """
    Check value = True
    iff.
        for all entries that fit css_selector: attr not NULL/defined
        and at least one entry
    """
    
    def check_unitary(self, webpage_check_dict_elt):
        if webpage_check_dict_elt[0]: # != None
            return True
        else:
            return False
    
    def check(self, webpage_check_dict):
        if len(webpage_check_dict[self.css_selector_][self.attr_name_]) == 0:
            return False

        return SEOCheck.check(self, webpage_check_dict)

class SEOCheckNotExist(SEOCheck):
    """
    Check value = True
    iff.
        specific_value defined: for all entries that fit css_selector: attr == specific_value (regex) (!=NULL)
        specific_value not defined: for all entries that fit css_selector: attr NULL/not defined
    """

    def __init__(self, css_selector, attr_name, pattern_specific_value, label=None, description=None):
        SEOCheck.__init__(self, css_selector, attr_name, label, description)
        
        if pattern_specific_value:
            self.regex_specific_value_ = re.compile(r'%s' % pattern_specific_value)
        else:
            self.regex_specific_value_ = None

    def check_unitary(self, webpage_check_dict_elt):
        if self.regex_specific_value_:
            if not webpage_check_dict_elt[0]: # attr not defined
                return False
            if len(self.regex_specific_value_.findall(webpage_check_dict_elt[1])) == 0: # attr != specific_value
                return False
        else:
            if webpage_check_dict_elt[0]: # attr defined
                return False
        return True
    
class SEOCheckLength(SEOCheck):
    """
    Check value = True
    iff.
        operator = '<': for all entries that fit css_selector: attr NULL or len(attr) >= length
        operator = '>': for all entries that fit css_selector: attr NULL or len(attr) <= length
    """
    def __init__(self, css_selector, attr_name, operator, length, label=None, description=None):
        # operator <: PB if measured <length
        # operator >: PB if measured >length
        SEOCheck.__init__(self, css_selector, attr_name, label, description)

        self.length_ = length
        self.operator_ = operator

    def check_unitary(self, webpage_check_dict_elt):
        if webpage_check_dict_elt[0] and ((self.operator_ == "<" and webpage_check_dict_elt[0] < self.length_) or (self.operator_ == ">" and webpage_check_dict_elt[0] > self.length_)):
            return False
        else:
            return True # not set => True, None is considered OK

class SEOCheckLengthBetween(SEOCheck):
    """
    Check value = True
    iff.
        for all entries that fit css_selector: attr NULL or length_min <= len(attr) <= length_max
    """
    def __init__(self, css_selector, attr_name, length_min, length_max, label=None, description=None):
        # PB if measured <length_min or measured >length_max
        # OK if measured in [length_min ; length_max]
        SEOCheck.__init__(self, css_selector, attr_name, label, description)

        self.length_min_ = length_min
        self.length_max_ = length_max

    def check_unitary(self, webpage_check_dict_elt):
        if webpage_check_dict_elt[0] and (webpage_check_dict_elt[0] < self.length_min_ or webpage_check_dict_elt[0] > self.length_max_):
            return False
        else:
            return True # not set => True, None is considered OK

