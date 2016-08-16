import ceph_cfg.util_which
import mock
import pytest


def find_executable_yes(executable):
    return '/usr/sbin/parted'


def find_executable_no(executable):
    return None


class Test_mdl_updater_lsblk_version(object):
    def setup(self):
        self.which = ceph_cfg.util_which.memoise_which('sdsdsd')


    @mock.patch('ceph_cfg.util_which.find_executable', find_executable_yes)
    def test_find_executable_yes(self):
        assert self.which.path == '/usr/sbin/parted'
        
        
    @mock.patch('ceph_cfg.util_which.find_executable', find_executable_no)
    def test_find_executable_no(self):
        with pytest.raises(ceph_cfg.util_which.ExecutableNotFound) as excinfo:
            self.which.path
        assert 'Could not find executable' in str(excinfo.value)
        assert 'sdsdsd' in str(excinfo.value)
