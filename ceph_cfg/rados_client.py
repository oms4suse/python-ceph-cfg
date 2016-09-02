# Import Python Libs
from __future__ import absolute_import
import logging
import shutil
import tempfile
import os
import pwd

# Local imports
from . import utils
from . import model
from . import mdl_updater
from . import service
from . import util_which
from . import keyring
from . import mdl_query
from . import constants


log = logging.getLogger(__name__)

class Error(Exception):
    """
    Error
    """

    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [str(a) for a in self.args])


class ctrl_rados_client(object):
    """
    Super class for all rados clients.
    """
    def __init__(self, **kwargs):
        # The path to the service binary
        self.path_service_bin = None
        # what we are starting
        self.ceph_client_id = kwargs.get("name")
        self.service_name = None
        self.model = model.model(**kwargs)
        self.model.init = "systemd"
        self.bootstrap_keyring_type = None
        self.keyring_service_capabilities = None
        self.keyring_service_path = None
        self.keyring_service_name = None


    def service_available(self):
        if self.path_service_bin is None:
            msg = "Can not setup '%s' as binary not found" % (self.service_name)
            log.error(msg)
            raise Error(msg)


    def update(self):
        self.updater = mdl_updater.model_updater(self.model)
        try:
            self.updater.defaults_refresh()
        except (utils.Error) as err:
            log.error(err)
        if self.model.cluster_name == None:
            log.error("Cluster name not found")
        log.debug("Cluster name %s" % (self.model.cluster_name))
        try:
            self.updater.load_confg(self.model.cluster_name)
        except (mdl_updater.Error) as err:
            log.error(err)
        try:
            self.updater.mon_members_refresh()
        except (mdl_updater.Error) as err:
            log.error(err)
        self.init_system = service.init_system(init_type=self.model.init)


    def activate(self):
        if self.ceph_client_id == None:
            raise Error("self.ceph_client_id not specified")
        if self.service_name == None:
            raise Error("self.service_name not specified")
        self.service_available()
        arguments = {
            'identifier' : self.ceph_client_id,
            'service' : self.service_name,
        }
        isrunning = self.init_system.is_running(**arguments)
        if not isrunning:
            self.init_system.start(**arguments)
        self.init_system.on_boot_enable(**arguments)



    def deactivate(self):
        if self.ceph_client_id == None:
            raise Error("self.ceph_client_id not specified")
        if self.service_name == None:
            raise Error("self.service_name not specified")
        arguments = {
            'identifier' : self.ceph_client_id,
            'service' : self.service_name,
        }
        isrunning = self.init_system.is_running(**arguments)
        if isrunning:
            self.init_system.stop(**arguments)
        self.init_system.on_boot_disable(**arguments)


    def create(self):
        self.prepare()
        self.activate()


    def destroy(self):
        self.deactivate()
        self.remove()


    def keyring_auth_remove(self):
        if self.ceph_client_id is None:
            raise Error("No client id specified")
        if self.bootstrap_keyring_type is None:
            raise Error("No bootstrap_keyring_type specified")
        keyringobj = keyring.keyring_facard(self.model)
        keyringobj.key_type = self.bootstrap_keyring_type
        arguments = [
            util_which.which_ceph.path,
            '--connect-timeout',
            '%s' % (constants.ceph_remote_call_timeout),
            '--cluster', self.model.cluster_name,
            '--name', keyringobj.keyring_identity_get(),
            '--keyring', keyringobj.keyring_path_get(),
            'auth', 'del', 'client.{name}'.format(name=self.ceph_client_id),
        ]

        output = utils.execute_local_command(arguments)
        if output["retcode"] != 0:
            raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                    " ".join(arguments),
                    output["retcode"],
                    output["stdout"],
                    output["stderr"])
                    )


    def keyring_service_create(self):
        if self.bootstrap_keyring_type is None:
            raise Error("No bootstrap_keyring_type specified")
        if self.keyring_service_capabilities is None:
            raise Error("No keyring_service_capabilities specified")
        if self.keyring_service_path is None:
            raise Error("No keyring_service_path specified")
        if self.keyring_service_name is None:
            raise Error("No keyring_service_path specified")
        if os.path.isfile(self.keyring_service_path):
            log.debug('Keyring already exists')
            return
        log.info("Make missing keyring:%s" % (self.keyring_service_path))
        keyringobj = keyring.keyring_facard(self.model)
        keyringobj.key_type = self.bootstrap_keyring_type
        oldmask = os.umask(int('077', 8))
        try:
            try:
                tmpd = tempfile.mkdtemp()
                key_path = os.path.join(tmpd, "keyring")
                arguments_prefix = [
                    util_which.which_ceph.path,
                    '--connect-timeout',
                    '%s' % (constants.ceph_remote_call_timeout),
                    '--cluster', self.model.cluster_name,
                    '--name', keyringobj.keyring_identity_get(),
                    '--keyring', keyringobj.keyring_path_get(),
                    'auth', 'get-or-create', self.keyring_service_name
                    ]
                arguments_postfix = [
                    '-o',
                    key_path
                ]
                arguments = arguments_prefix + self.keyring_service_capabilities + arguments_postfix
                output = utils.execute_local_command(arguments)
                if output["retcode"] != 0:
                    raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                            " ".join(arguments),
                            output["retcode"],
                            output["stdout"],
                            output["stderr"])
                            )
                shutil.copy(key_path, self.keyring_service_path)
                q = mdl_query.mdl_query(self.model)
                ceph_daemon_user = q.ceph_daemon_user()
                if ceph_daemon_user != 'root':
                    pwd_struct = pwd.getpwnam(ceph_daemon_user)
                    uid = pwd_struct.pw_uid
                    gid = pwd_struct.pw_gid
                    os.chown(self.keyring_service_path, uid, gid)
            finally:
                shutil.rmtree(tmpd)
        finally:
            os.umask(oldmask)
