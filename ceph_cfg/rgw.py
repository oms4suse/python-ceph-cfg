# Import Python Libs
from __future__ import absolute_import
import os
import logging
import shutil

# Local imports
from . import constants
from . import util_which
from . import keyring
from . import mdl_updater_remote
from . import rados_client


log = logging.getLogger(__name__)

class Error(Exception):
    """
    Error
    """

    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [str(a) for a in self.args])


class rgw_ctrl(rados_client.ctrl_rados_client):
    def __init__(self, **kwargs):
        super(rgw_ctrl, self).__init__(**kwargs)
        self.service_name = "ceph-radosgw"
        # Set path to rgw binary
        self.path_service_bin = util_which.which_ceph_rgw.path
        self.bootstrap_keyring_type = 'rgw'
        self.keyring_service_name = 'client.{name}'.format(name=self.ceph_client_id)
        self.keyring_service_capabilities = [
            'osd', 'allow rwx',
            'mon', 'allow rw'
            ]

    def _set_rgw_path_lib(self):
        if self.ceph_client_id == None:
            raise Error("rgw name not specified")
        self.rgw_path_lib = '{path}/{cluster}-{name}'.format(
            path=constants._path_ceph_lib_rgw,
            cluster=self.model.cluster_name,
            name=self.ceph_client_id
            )


    def rgw_pools_missing(self):
        requiredPools = set([".rgw",
                ".rgw.control",
                ".rgw.gc",
                ".log",
                ".intent-log",
                ".usage",
                ".users",
                ".users.email",
                ".users.swift",
                ".users.uid"
            ])
        mur = mdl_updater_remote.model_updater_remote(self.model)
        can_connect = mur.connect()
        if not can_connect:
            raise Error("Cant connect to cluster.")
        mur.pool_list()
        if self.model.pool_list == None:
            log.error("Failed to list available pools")
            return False
        foundnames = set()
        for pool in self.model.pool_list:
            foundnames.add(pool)
        return list(requiredPools.difference(foundnames))


    def rgw_pools_create(self):
        rc = True
        mur = mdl_updater_remote.model_updater_remote(self.model)
        can_connect = mur.connect()
        if not can_connect:
            raise Error("Cant connect to cluster.")
        for name in self.rgw_pools_missing():
            log.info("Adding missing pool:%s" % (name))
            try:
                mur.pool_add(name, pg_num=16)
            except (mdl_updater_remote.Error) as err:
                log.error(err)
                log.error("Failed to add pool '%s'" % (name))
                rc = False
        return rc


    def prepare(self):
        # Due to the way keyring profiles work and the init scripts for rgw we need to
        # force users to only create rgw with a 'rgw.' prefix. The reason we dont hide
        # this from the user is due to both the systemd files and rgw deployments may
        # exist without the prefix if the bootstrap keyring was not used in the key
        # creation for the rgw service.
        if not self.ceph_client_id.startswith("rgw."):
            raise Error("rgw name must start with 'rgw.'")
        self.service_available()
        self._set_rgw_path_lib()
        path_bootstrap_keyring = keyring._get_path_keyring_rgw(self.model.cluster_name)
        if not os.path.isfile(path_bootstrap_keyring):
            raise Error("Keyring not found at %s" % (path_bootstrap_keyring))
        if not os.path.isdir(self.rgw_path_lib):
            log.info("Make missing directory:%s" % (self.rgw_path_lib))
            os.makedirs(self.rgw_path_lib)
        self.keyring_service_path = os.path.join(self.rgw_path_lib, 'keyring')
        self.keyring_service_create()


    def remove(self):
        self._set_rgw_path_lib()
        if not os.path.isdir(self.rgw_path_lib):
            return
        rgw_path_keyring = os.path.join(self.rgw_path_lib, 'keyring')
        if os.path.isfile(rgw_path_keyring):
            log.info("Remove from auth list keyring:%s" % (rgw_path_keyring))
            try:
                self.keyring_auth_remove()
            except Error:
                log.error("Failed to remote from auth list")
        removetree = "%s/" % (self.rgw_path_lib)
        log.info("Remove directory content:%s" % (removetree))
        shutil.rmtree(removetree)
