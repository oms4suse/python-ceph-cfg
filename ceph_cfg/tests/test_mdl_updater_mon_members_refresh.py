import pytest
import ceph_cfg.model
import ceph_cfg.mdl_updater

import tempfile
import os.path
import shutil


class Test_mon_members_refresh(object):
    def setup(self):
        '''
        Make updater
        Make temp directory for tests.
        '''
        self.model = ceph_cfg.model.model()
        self.updater = ceph_cfg.mdl_updater.model_updater(self.model)
        self.test_dir = tempfile.mkdtemp()


    def teardown(self):
        """
        Remove temp directory and content
        """
        shutil.rmtree(self.test_dir)


    def test_good_config_normal(self):
        file_name = os.path.join(self.test_dir,"file")
        with open(file_name, 'wt') as fp:
            fp.write("[global]\n")
            fp.write("fsid = eaac9695-4265-4ca8-ac2a-f3a479c559b1\n")
            fp.write("mon initial members = osceph-02, osceph-03, osceph-04\n")
            fp.write("mon host = 192.168.43.60,192.168.43.96,192.168.43.80\n")
            fp.write("auth cluster required = cephx\n")
            fp.write("auth service required = cephx\n")
            fp.write("auth client required = cephx\n")
        self.model.ceph_conf.read(file_name)
        self.updater.mon_members_refresh()
        assert self.model.mon_members == [
                ('osceph-02', '192.168.43.60'),
                ('osceph-03', '192.168.43.96'),
                ('osceph-04', '192.168.43.80')
            ]
        

    def test_good_config_underscore(self):
        file_name = os.path.join(self.test_dir,"file")
        with open(file_name, 'wt') as fp:
            fp.write("[global]\n")
            fp.write("fsid = eaac9695-4265-4ca8-ac2a-f3a479c559b1\n")
            fp.write("mon_initial_members = osceph-02, osceph-03, osceph-04\n")
            fp.write("mon_host = 192.168.43.60,192.168.43.96,192.168.43.80\n")
            fp.write("auth_cluster_required = cephx\n")
            fp.write("auth_service_required = cephx\n")
            fp.write("auth_client_required = cephx\n")
        self.model.ceph_conf.read(file_name)
        self.updater.mon_members_refresh()
        assert self.model.mon_members == [
                ('osceph-02', '192.168.43.60'),
                ('osceph-03', '192.168.43.96'),
                ('osceph-04', '192.168.43.80')
            ]


    def test_bad_config_section(self):
        file_name = os.path.join(self.test_dir,"file")
        with open(file_name, 'wt') as fp:
            fp.write("[bad_section]\n")
            fp.write("fsid = eaac9695-4265-4ca8-ac2a-f3a479c559b1\n")
            fp.write("mon_initial_members = osceph-02, osceph-03, osceph-04\n")
            fp.write("mon_host = 192.168.43.60,192.168.43.96,192.168.43.80\n")
            fp.write("auth_cluster_required = cephx\n")
            fp.write("auth_service_required = cephx\n")
            fp.write("auth_client_required = cephx\n")
        self.model.ceph_conf.read(file_name)
        with pytest.raises(ceph_cfg.mdl_updater.Error) as excinfo:
            self.updater.mon_members_refresh()
        assert '[global]' in str(excinfo.value)


    def test_bad_config_missing_mon_initial_members(self):
        file_name = os.path.join(self.test_dir,"file")
        with open(file_name, 'wt') as fp:
            fp.write("[global]\n")
            fp.write("fsid = eaac9695-4265-4ca8-ac2a-f3a479c559b1\n")
            fp.write("mon_host = 192.168.43.60,192.168.43.96,192.168.43.80\n")
            fp.write("auth_cluster_required = cephx\n")
            fp.write("auth_service_required = cephx\n")
            fp.write("auth_client_required = cephx\n")
        self.model.ceph_conf.read(file_name)
        with pytest.raises(ceph_cfg.mdl_updater.Error) as excinfo:
            self.updater.mon_members_refresh()
        assert 'mon_initial_members' in str(excinfo.value)


    def test_bad_config_missing_mon_host(self):
        file_name = os.path.join(self.test_dir,"file")
        with open(file_name, 'wt') as fp:
            fp.write("[global]\n")
            fp.write("fsid = eaac9695-4265-4ca8-ac2a-f3a479c559b1\n")
            fp.write("mon_initial_members = osceph-02, osceph-03, osceph-04\n")
            fp.write("auth_cluster_required = cephx\n")
            fp.write("auth_service_required = cephx\n")
            fp.write("auth_client_required = cephx\n")
        self.model.ceph_conf.read(file_name)
        with pytest.raises(ceph_cfg.mdl_updater.Error) as excinfo:
            self.updater.mon_members_refresh()
        
        assert 'mon_host' in str(excinfo.value)


    def test_bad_config_mon_not_equal(self):
        file_name = os.path.join(self.test_dir,"file")
        with open(file_name, 'wt') as fp:
            fp.write("[global]\n")
            fp.write("fsid = eaac9695-4265-4ca8-ac2a-f3a479c559b1\n")
            fp.write("mon_initial_members = osceph-02, osceph-03, osceph-04\n")
            fp.write("mon_host = 192.168.43.60,192.168.43.96\n")
            fp.write("auth_cluster_required = cephx\n")
            fp.write("auth_service_required = cephx\n")
            fp.write("auth_client_required = cephx\n")
        self.model.ceph_conf.read(file_name)
        with pytest.raises(ceph_cfg.mdl_updater.Error) as excinfo:
            self.updater.mon_members_refresh()
        assert "different numbers of mon 'names' and ip addresses" in str(excinfo.value)
