# Import Python Libs
from __future__ import absolute_import
import os
import logging
import shutil

# Local imports
from . import constants
from . import keyring
from . import rados_client
from . import util_which


log = logging.getLogger(__name__)

class Error(Exception):
    """
    Error
    """

    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [str(a) for a in self.args])


class mds_ctrl(rados_client.ctrl_rados_client):
    def __init__(self, **kwargs):
        super(mds_ctrl, self).__init__(**kwargs)
        self.service_name = "ceph-mds"
        # Set path to mds binary
        self.path_service_bin = util_which.which_ceph_mds.path
        self.port = kwargs.get("port")
        self.addr = kwargs.get("addr")
        self.bootstrap_keyring_type = 'mds'
        self.keyring_service_name = 'mds.{name}'.format(name=self.ceph_client_id)
        self.keyring_service_capabilities = [
            'osd', 'allow rwx',
            'mds', 'allow',
            'mon', 'allow profile mds',
            ]


    def _set_mds_path_lib(self):
        if self.ceph_client_id == None:
            raise Error("mds name not specified")
        self.mds_path_lib = '{path}/{cluster}-{name}'.format(
            path=constants._path_ceph_lib_mds,
            cluster=self.model.cluster_name,
            name=self.ceph_client_id
            )

    def _set_path_systemd_env(self):
        self.model.path_systemd_env = "{lib_dir}/systemd/".format(
            lib_dir=constants._path_ceph_lib_mds,
            )

    def _set_mds_path_env(self):
        if self.ceph_client_id == None:
            raise Error("mds name not specified")
        if self.model.cluster_name == None:
            raise Error("cluster_name not specified")
        if self.model.path_systemd_env == None:
            raise Error("self.model.path_systemd_env not specified")
        self.model.mds_path_env = "{path_systemd_env}/{name}".format(
            name=self.ceph_client_id,
            path_systemd_env=self.model.path_systemd_env
            )

    def update(self):
        super(mds_ctrl, self).update()
        self._set_mds_path_lib()
        self._set_path_systemd_env()
        self._set_mds_path_env()


    def prepare(self):
        self.service_available()
        if not os.path.isdir(self.model.path_systemd_env):
            log.info("mkdir %s" % (self.model.path_systemd_env))
            os.makedirs(self.model.path_systemd_env)
        if not os.path.isdir(self.mds_path_lib):
            log.info("mkdir %s" % (self.mds_path_lib))
            os.makedirs(self.mds_path_lib)

        self.keyring_service_path = os.path.join(self.mds_path_lib, 'keyring')
        self.keyring_service_create()


    def remove(self):
        if os.path.isfile(self.model.mds_path_env):
            log.info("removing:%s" % (self.model.mds_path_env))
            os.remove(self.model.mds_path_env)
        if not os.path.isdir(self.mds_path_lib):
            return
        mds_path_keyring = os.path.join(self.mds_path_lib, 'keyring')
        if os.path.isfile(mds_path_keyring):
            self.keyring_auth_remove()
        shutil.rmtree(self.mds_path_lib)




    def make_env(self):
        if os.path.isfile(self.model.mds_path_env):
            return
        data_list = []
        data_list.append('BIND_IPV4="{ipv4}"\n'.format(ipv4=self.addr))
        data_list.append('BIND_PORT="{port}"\n'.format(port=self.port))
        data_list.append('CLUSTER="{cluster}"\n'.format(cluster=self.model.cluster_name))
        with open(self.model.mds_path_env, 'w+') as f:
            for data in data_list:
                f.write(data)


    def activate(self):
        if self.ceph_client_id == None:
            raise Error("name not specified")
        if self.port == None:
            raise Error("port not specified")
        if self.addr == None:
            raise Error("addr not specified")
        if self.model.path_systemd_env == None:
            raise Error("self.model.path_systemd_env not specified")
        if self.model.mds_path_env == None:
            raise Error("self.model.mds_path_env not specified")
        if not os.path.isdir(self.model.path_systemd_env):
            raise Error("self.model.path_systemd_env not specified")

        if not os.path.isfile(self.model.mds_path_env):
            log.info("Making file:%s" % (self.model.mds_path_env))
            self.make_env()
        super(mds_ctrl, self).activate()
