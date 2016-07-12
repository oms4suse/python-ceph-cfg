import logging


import utils
import model
import mdl_updater
import service
import util_which


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
    Super class.
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


    def service_available(self):
        if self.path_service_bin is None:
            msg = "Can not setup '%s' as binary not found" % (self.service_name)
            log.error(msg)
            raise Error(msg)


    def update(self):
        self.updater = mdl_updater.model_updater(self.model)
        self.updater.hostname_refresh()
        try:
            self.updater.defaults_refresh()
        except utils.Error, e:
            log.error(e)
        if self.model.cluster_name == None:
            log.error("Cluster name not found")
        log.debug("Cluster name %s" % (self.model.cluster_name))
        try:
            self.updater.load_confg(self.model.cluster_name)
        except mdl_updater.Error, e:
            log.error(e)
        try:
            self.updater.mon_members_refresh()
        except mdl_updater.Error, e:
            log.error(e)
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
        if self.ceph_client_id == None:
            raise Error("No client id specified")
        if self.bootstrap_keyring_type == None:
            raise Error("No bootstrap_keyring_type specified")
        keyringobj = keyring.keyring_facard(self.model)
        keyringobj.key_type = self.bootstrap_keyring_type
        arguments = [
            util_which.which_ceph.path,
            '--connect-timeout',
            '5',
            '--cluster', self.model.cluster_name,
            '--name', keyring_obj.keyring_identity_get()
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
