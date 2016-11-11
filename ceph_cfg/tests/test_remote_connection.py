import pytest
import ceph_cfg.model
import ceph_cfg.keyring
import ceph_cfg.remote_connection
import mock


def mock_connection_fail(*args):
    output= {
        'stdout' : "Could not connect\n",
        'stderr' : "",
        'retcode' : 1
        }
    return output


class Test_remote_connection(object):
    def setup(self):
        self.mdl = ceph_cfg.model.model()
        self.mdl.cluster_name = "ceph"
        self.remote_connection = ceph_cfg.remote_connection.connection(self.mdl)


    def test_arguments_get_connection(self):
        self.mdl.connection.keyring_type = "admin"
        self.mdl.connection.keyring_path = "/etc/ceph/ceph.client.admin.keyring"
        self.mdl.connection.keyring_identity = "client.admin"
        args_list = self.remote_connection.arguments_get()
        assert self.mdl.connection.keyring_path in args_list
        assert self.mdl.connection.keyring_identity in args_list


    @mock.patch('ceph_cfg.utils.execute_local_command', mock_connection_fail)
    def test_arguments_get_no_connection(self):
        with pytest.raises(ceph_cfg.remote_connection.Error) as excinfo:
            self.remote_connection.arguments_get()
        assert 'Failed to connect to cluster' in str(excinfo.value)
