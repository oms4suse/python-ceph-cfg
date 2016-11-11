from ceph_cfg.util_configparser import ConfigParserCeph as ConfigParser
import tempfile
import os.path
import shutil


class Test_util_configparser(object):
    def setup(self):
        """
        Make temp directory for tests.
        """
        self.test_dir = tempfile.mkdtemp()


    def teardown(self):
        """
        Remove temp directory and content
        """
        shutil.rmtree(self.test_dir)

        
    def test_whitespace_none(self):
        config = ConfigParser()
        file_name = os.path.join(self.test_dir,"file")
        with open(file_name, 'wt') as fp:
            fp.write("[mysqld]\n")
            fp.write("user2 = mysql")
        config.read(file_name)
        value = config.get("mysqld", "user2")
        assert value == "mysql"


    def test_whitespace(self):
        config = ConfigParser()
        file_name = os.path.join(self.test_dir,"file")
        with open(file_name, 'wt') as fp:
            fp.write("[mysqld]\n")
            fp.write("user 2 = mysql\n")
        config.read(file_name)
        value = config.get("mysqld", "user_2")
        assert value == "mysql"


    def test_whitespace_two(self):
        config = ConfigParser()
        file_name = os.path.join(self.test_dir,"file")
        with open(file_name, 'wt') as fp:
            fp.write("[mysqld]\n")
            fp.write("user 2 3 = mysql\n")
        config.read(file_name)
        value = config.get("mysqld", "user_2_3")
        assert value == "mysql"


    def test_whitespace_as_underscore(self):
        config = ConfigParser()
        file_name = os.path.join(self.test_dir,"file")
        with open(file_name, 'wt') as fp:
            fp.write("[mysqld]\n")
            fp.write("user_2 = mysql\n")
        config.read(file_name)
        value = config.get("mysqld", "user_2")
        assert value == "mysql"


    def test_no_global_section(self):
        config = ConfigParser()
        file_name = os.path.join(self.test_dir,"file")
        with open(file_name, 'wt') as fp:
            fp.write("user2 = mysql")
        config.read(file_name)
        value = config.get("global", "user2")
        assert value == "mysql"
