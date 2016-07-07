import string
import ConfigParser

class ConfigParserCeph(ConfigParser.ConfigParser):

    def optionxform(self, s):
        """
        Make config files with white space use '_'
        """
        s = string.replace(s.strip(), ' ', '_')
        return s

