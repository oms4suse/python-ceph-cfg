import ceph_cfg.utils
import ceph_cfg.model
import ceph_cfg.mdl_updater

import mock
import pytest


lsblk_args_new = [
    "--ascii",
    "--output-all",
    "--pairs",
    "--paths",
    "--bytes"
    ]


lsblk_args_old = [
    "--ascii",
    "--output",
    "NAME,FSTYPE,MOUNTPOINT,PARTLABEL,PARTUUID,PKNAME,ROTA,RQ-SIZE,SCHED,SIZE,TYPE,UUID,VENDOR",
    "--pairs",
    "--paths",
    "--bytes"
    ]


def mock_lsblk_version_2_25(command_attrib_list):
    output= {
        'stdout' : "lsblk from util-linux 2.25\n",
        'stderr' : "",
        'retcode' : 0
        }
    return output


def mock_lsblk_version_2_23(command_attrib_list):
    output= {
        'stdout' : "lsblk from util-linux 2.23\n",
        'stderr' : "",
        'retcode' : 0
        }
    return output


class Test_mdl_updater_lsblk_version(object):
    def setup(self):
        """
        Make model and updater
        """
        self.model = ceph_cfg.model.model()
        self.updater = ceph_cfg.mdl_updater.model_updater(self.model)


    @mock.patch('ceph_cfg.utils.execute_local_command', mock_lsblk_version_2_25)
    def test_lsblk_version_2_25(self):
        self.updater.lsblk_version_refresh()
        assert self.model.lsblk_version.major == 2
        assert self.model.lsblk_version.minor == 25
        assert self.model.lsblk_version.revision == 0


    @mock.patch('ceph_cfg.utils.execute_local_command', mock_lsblk_version_2_23)
    def test_lsblk_version_2_23(self):
        self.updater.lsblk_version_refresh()
        assert self.model.lsblk_version.major == 2
        assert self.model.lsblk_version.minor == 23
        assert self.model.lsblk_version.revision == 0


    def test_lsblk_args_very_old(self):
        self.model.lsblk_version.major = 2
        self.model.lsblk_version.minor = 22
        self.model.lsblk_version.revision = 0
        with pytest.raises(ceph_cfg.mdl_updater.Error):
            self.updater._lsblk_arguements()


    def test_lsblk_args_old(self):
        self.model.lsblk_version.major = 2
        self.model.lsblk_version.minor = 23
        self.model.lsblk_version.revision = 0
        args = self.updater._lsblk_arguements()
        assert args == lsblk_args_old


    def test_lsblk_args_new(self):
        self.model.lsblk_version.major = 2
        self.model.lsblk_version.minor = 25
        self.model.lsblk_version.revision = 0
        args = self.updater._lsblk_arguements()
        assert args == lsblk_args_new
