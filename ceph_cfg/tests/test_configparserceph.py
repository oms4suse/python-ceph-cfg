from ceph_cfg.util_configparser import ConfigParserCeph as ConfigParser
import io

class Test_util_configparser(object):

    def test_whitespace_none(self):
        sample_config = """
[mysqld]
user2 = mysql
"""
        config = ConfigParser()
        config.readfp(io.BytesIO(sample_config))
        value = config.get("mysqld", "user2")
        assert value == "mysql"


    def test_whitespace(self):
        sample_config = """
[mysqld]
user 2 = mysql
"""
        config = ConfigParser()
        config.readfp(io.BytesIO(sample_config))
        value = config.get("mysqld", "user_2")
        assert value == "mysql"

    def test_whitespace_two(self):
        sample_config = """
[mysqld]
user 2 3 = mysql
"""
        config = ConfigParser()
        config.readfp(io.BytesIO(sample_config))
        value = config.get("mysqld", "user_2_3")
        assert value == "mysql"


    def test_whitespace_as_underscore(self):
        sample_config = """
[mysqld]
user_2 = mysql
"""
        config = ConfigParser()
        config.readfp(io.BytesIO(sample_config))
        value = config.get("mysqld", "user_2")
        assert value == "mysql"
