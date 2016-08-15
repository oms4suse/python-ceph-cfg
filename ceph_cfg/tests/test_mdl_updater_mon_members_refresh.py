import pytest
import ceph_cfg.model
import ceph_cfg.mdl_updater
import io


class Test_mon_members_refresh(object):
    def setup(self):
        '''
        Make updater
        '''
        self.model = ceph_cfg.model.model()
        self.updater = ceph_cfg.mdl_updater.model_updater(self.model)


    def test_good_config_normal(self):
        sample_config = '''
[global]
fsid = eaac9695-4265-4ca8-ac2a-f3a479c559b1
mon initial members = osceph-02, osceph-03, osceph-04
mon host = 192.168.43.60,192.168.43.96,192.168.43.80
auth cluster required = cephx
auth service required = cephx
auth client required = cephx
'''
        self.model.ceph_conf.readfp(io.BytesIO(sample_config))
        self.updater.mon_members_refresh()
        assert self.model.mon_members == [
                ('osceph-02', '192.168.43.60'),
                ('osceph-03', '192.168.43.96'),
                ('osceph-04', '192.168.43.80')
            ]
        

    def test_good_config_underscore(self):
        sample_config = '''
[global]
fsid = eaac9695-4265-4ca8-ac2a-f3a479c559b1
mon_initial_members = osceph-02, osceph-03, osceph-04
mon_host = 192.168.43.60,192.168.43.96,192.168.43.80
auth_cluster_required = cephx
auth_service_required = cephx
auth_client_required = cephx
'''
        self.model.ceph_conf.readfp(io.BytesIO(sample_config))
        self.updater.mon_members_refresh()
        assert self.model.mon_members == [
                ('osceph-02', '192.168.43.60'),
                ('osceph-03', '192.168.43.96'),
                ('osceph-04', '192.168.43.80')
            ]


    def test_bad_config_section(self):
        sample_config = '''
[bad_section]
fsid = eaac9695-4265-4ca8-ac2a-f3a479c559b1
mon_initial_members = osceph-02, osceph-03, osceph-04
mon_host = 192.168.43.60,192.168.43.96,192.168.43.80
auth_cluster_required = cephx
auth_service_required = cephx
auth_client_required = cephx
'''
        self.model.ceph_conf.readfp(io.BytesIO(sample_config))
        with pytest.raises(ceph_cfg.mdl_updater.Error) as excinfo:
            self.updater.mon_members_refresh()
        assert '[global]' in str(excinfo.value)


    def test_bad_config_missing_mon_initial_members(self):
        sample_config = '''
[global]
fsid = eaac9695-4265-4ca8-ac2a-f3a479c559b1
mon_host = 192.168.43.60,192.168.43.96,192.168.43.80
auth_cluster_required = cephx
auth_service_required = cephx
auth_client_required = cephx
'''
        self.model.ceph_conf.readfp(io.BytesIO(sample_config))
        with pytest.raises(ceph_cfg.mdl_updater.Error) as excinfo:
            self.updater.mon_members_refresh()
        assert 'mon_initial_members' in str(excinfo.value)


    def test_bad_config_missing_mon_host(self):
        sample_config = '''
[global]
fsid = eaac9695-4265-4ca8-ac2a-f3a479c559b1
mon_initial_members = osceph-02, osceph-03, osceph-04
auth_cluster_required = cephx
auth_service_required = cephx
auth_client_required = cephx
'''
        self.model.ceph_conf.readfp(io.BytesIO(sample_config))
        with pytest.raises(ceph_cfg.mdl_updater.Error) as excinfo:
            self.updater.mon_members_refresh()
        
        assert 'mon_host' in str(excinfo.value)


    def test_bad_config_mon_not_equal(self):
        sample_config = '''
[global]
fsid = eaac9695-4265-4ca8-ac2a-f3a479c559b1
mon_initial_members = osceph-02, osceph-03, osceph-04
mon_host = 192.168.43.60,192.168.43.96
auth_cluster_required = cephx
auth_service_required = cephx
auth_client_required = cephx
'''
        self.model.ceph_conf.readfp(io.BytesIO(sample_config))
        with pytest.raises(ceph_cfg.mdl_updater.Error) as excinfo:
            self.updater.mon_members_refresh()
        assert "different numbers of mon 'names' and ip addresses" in str(excinfo.value)
