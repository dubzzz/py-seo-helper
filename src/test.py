class Test:
    def __init__(self, title, description, level):
        self.title_ = title
        self.description_ = description
        self.level_ = level

        self.passed_ = True
        self.failures_ = list()

    def append(self, webpage):
        """
        Append a webpage to failures
        Passed = False
        """
        
        self.passed_ = False
        self.failures_.append(webpage)

    def set_passed(self, passed):
        self.passed_ = passed
    
    def get_title(self):
        return self.title_
    
    def get_description(self):
        return self.description_

    def get_level(self):
        return self.level_
    
    def get_level_str(self):
        severities = ["Critical", "High", "Medium", "Low"]
        if self.level_ >= 0 and self.level_ < 4:
            return severities[self.level_]
        return "Unknown"

    def get_passed(self):
        return self.passed_

    def get_failures(self):
        return self.failures_

