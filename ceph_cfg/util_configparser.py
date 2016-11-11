from io import StringIO
try:
    import ConfigParser
except:
    import configparser as ConfigParser


class ConfigParserCeph(ConfigParser.ConfigParser):

    def optionxform(self, s):
        """
        Make config files with white space use '_'
        """
        stripped = s.strip()
        replaced = stripped.replace(' ', '_')
        return replaced


    def _MissingSectionHeaderError_read(self,file_name):
        vfile = StringIO(u'[global]\n%s' % open(file_name).read())
        return ConfigParser.ConfigParser.readfp(self, vfile)


    def read(self, filenames):
        """Read and parse a filename or a list of filenames.

        Files that cannot be opened are silently ignored; this is
        designed so that you can specify a list of potential
        configuration file locations (e.g. current directory, user's
        home directory, systemwide directory), and all existing
        configuration files in the list will be read.  A single
        filename may also be given.

        Return list of successfully read files.
        """
        if isinstance(filenames, ("".__class__, u"".__class__)):
            filenames = [filenames]
        read_ok = []
        for filename in filenames:
            try:
                fp = open(filename)
            except IOError:
                continue
            try:
                self._read(fp, filename)
            except ConfigParser.MissingSectionHeaderError:
                self._MissingSectionHeaderError_read(filename)
            fp.close()
            read_ok.append(filename)
        return read_ok
