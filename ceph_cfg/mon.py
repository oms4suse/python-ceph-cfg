# Import Python Libs
from __future__ import absolute_import
import logging
import os
import os.path
import pwd
import tempfile
import shutil
import time
import json

# Local imports
from . import keyring
from . import mdl_query
from . import mdl_updater
from . import model
from . import presenter
from . import utils
from . import service
from . import util_which
from . import constants
from . import ops_mon


log = logging.getLogger(__name__)


def Property(func):
    return property(**func())


class Error(Exception):
    """
    Error
    """
    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [str(a) for a in self.args])


class ErrorNotMon(Error):
    """
    Error when its not a mon
    """
    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [str(a) for a in self.args])


class mon_implementation_base(object):
    def __init__(self, mdl):
        self.model = mdl
        self.model.init = "systemd"
        self.init_system = service.init_system(init_type=self.model.init)


    def _execute(self, arguments):
        return utils.execute_local_command(arguments)


    def _create_monmap(self, path_monmap):
        """
        create_monmap file
        """
        if not os.path.isfile(path_monmap):
            arguments = [
                "monmaptool",
                "--create",
                "--fsid",
                self.model.cluster_uuid,
                path_monmap
                ]
            output = utils.execute_local_command(arguments)
            if output["retcode"] != 0:
                    raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                        " ".join(arguments),
                        output["retcode"],
                        output["stdout"],
                        output["stderr"])
                        )
            for name, addr in self.model.mon_members:
                arguments = [
                        "monmaptool",
                        "--add",
                        name,
                        addr,
                        path_monmap
                        ]
                output = utils.execute_local_command(arguments)
                if output["retcode"] != 0:
                    raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                        " ".join(arguments),
                        output["retcode"],
                        output["stdout"],
                        output["stderr"])
                        )
        return True



    def _mon_status(self, **kwargs):
        service_name = kwargs.get("mon_name")
        if service_name is None:
            raise Error("Service name for mon is not specified as 'mon_name'")
        if self.model.cluster_name is None:
            raise Error("cluster_name not set")
        arguments = [
            "ceph",
            "--cluster=%s" % (self.model.cluster_name),
            "--admin-daemon",
            "/var/run/ceph/ceph-mon.%s.asok" % (service_name),
            "mon_status"
            ]
        output = utils.execute_local_command(arguments)
        if output["retcode"] != 0:
            raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                        " ".join(arguments),
                        output["retcode"],
                        output["stdout"],
                        output["stderr"])
                        )
        self.model.mon_status = json.loads(output['stdout'])



    def mon_is(self, **kwargs):
        """
        Is this a mon node

        mon_name
            Set the mon service name

        cluster_name
            Set the cluster name. Defaults to "ceph".

        cluster_uuid
            Set the cluster UUID. Defaults to value found in ceph config file.
        """
        service_name = kwargs.get("mon_name")
        if service_name is None:
            raise Error("Service name for mon is not specified as 'mon_name'")
        for name, addr in self.model.mon_members:
            if name == service_name:
                return True
        return False


    def status(self, **kwargs):
        """
        Get status from mon deamon

        cluster_uuid
            Set the cluster UUID. Defaults to value found in ceph config file.

        cluster_name
            Set the cluster name. Defaults to "ceph".
        """
        self._mon_status(**kwargs)
        p = presenter.mdl_presentor(self.model)
        return p.mon_status()


    def quorum(self, **kwargs):
        """
        Is mon deamon in quorum

        Args:
            **kwargs: Arbitrary keyword arguments.
                cluster_uuid
                    Set the cluster UUID. Defaults to value found in ceph
                    config file.
                cluster_name
                    Set the cluster name. Defaults to "ceph".
        """
        self._mon_status(**kwargs)
        q = mdl_query.mdl_query(self.model)
        return q.mon_quorum()


    def _create_check_responding(self, **kwargs):
        """
        Check the mon service is runnign and responding.
        """
        if not self.active(**kwargs):
            raise Error("mon service has died.")
        try:
            self._mon_status(**kwargs)
        except mdl_updater.Error:
            return False
        return True


    def _create_check_retry(self, **kwargs):
        """
        Check the mon service is started and responding with time out.

        On heavily overloaded hardware it can takes a while for the mon service
        to start
        """
        # Number of seconds before a time out.
        timeout = 60
        time_start = time.clock()
        time_end = time_start + timeout
        if self._create_check_responding(**kwargs):
            return True
        while time.clock() < time_end:
            log.info("Mon service did not start up, waiting.")
            time.sleep(5)
            log.info("Retrying mon service.")
            if self._create_check_responding(**kwargs):
                return True
        log.error("Timed out starting mon service")
        raise Error("Failed to get mon service status after '%s' seconds." % (timeout))


    def create(self, **kwargs):
        """
        Create a mon node

        Args:
            **kwargs: Arbitrary keyword arguments.
                cluster_uuid
                    Set the cluster UUID. Defaults to value found in ceph
                    config file.
                cluster_name
                    Set the cluster name. Defaults to "ceph".
        """
        service_name = kwargs.get("mon_name")
        if service_name is None:
            raise Error("Service name for mon is not specified as 'mon_name'")
        if util_which.which_ceph_mon.path is None:
            raise Error("Could not find executable 'ceph-mon'")

        path_mon_dir_postfix = "/%s-%s" % (
                self.model.cluster_name,
                service_name
            )
        path_mon_dir = constants._path_ceph_lib_mon + path_mon_dir_postfix
        path_done_file = path_mon_dir + "/done"
        keyring_facard = keyring.keyring_facard(self.model)
        keyring_facard.key_type = "admin"
        path_admin_keyring = keyring_facard.keyring_path_get()
        keyring_facard.key_type = "mon"
        keyring_path_mon = keyring_facard.keyring_path_get()

        if os.path.isfile(path_done_file):
            log.debug("Mon done file exists:%s" % (path_done_file))
            if self.active(**kwargs):
                return True
            arguments = [
                util_which.which_systemctl.path,
                "restart",
                "ceph-mon@%s" % (service_name)
                ]
            output = utils.execute_local_command(arguments)
            if output["retcode"] != 0:
                raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                    " ".join(arguments),
                    output["retcode"],
                    output["stdout"],
                    output["stderr"])
                    )

            # Error is servcie wont start
            if not self.active(**kwargs):
                 raise Error("Failed to start monitor")
            return True

        if not os.path.isfile(keyring_path_mon):
            raise Error("Mon keyring missing")
        if not os.path.isfile(path_admin_keyring):
            raise Error("Admin keyring missing")

        try:
            tmpd = tempfile.mkdtemp()
            log.info("Create temp directory %s" %(tmpd))
            os.chown(tmpd, self.uid, self.gid)
            # In 'tmpd' we make the monmap and keyring.
            key_path = os.path.join(tmpd,"keyring")
            path_monmap = os.path.join(tmpd,"monmap")
            log.info("Create monmap %s" % (path_monmap))
            self._create_monmap(path_monmap)
            os.chown(path_monmap, self.uid, self.gid)
            arguments = [
                util_which.which_ceph_authtool.path,
                "--create-keyring",
                key_path,
                "--import-keyring",
                keyring_path_mon,
                ]
            output = utils.execute_local_command(arguments)
            if output["retcode"] != 0:
                raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                    " ".join(arguments),
                    output["retcode"],
                    output["stdout"],
                    output["stderr"]
                    ))
            arguments = [
                util_which.which_ceph_authtool.path,
                key_path,
                "--import-keyring",
                path_admin_keyring,
                ]
            output = utils.execute_local_command(arguments)
            if output["retcode"] != 0:
                raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                    " ".join(arguments),
                    output["retcode"],
                    output["stdout"],
                    output["stderr"]
                    ))
            # Now chown the new file
            os.chown(key_path, self.uid, self.gid)
            # Now clean the install area
            if os.path.isdir(path_mon_dir):
                log.info("Remove directory content %s" %(path_mon_dir))
                shutil.rmtree(path_mon_dir)
            if not os.path.isdir(path_mon_dir):
                log.info("Make directory %s" %(path_mon_dir))
                os.makedirs(path_mon_dir)
                os.chown(path_mon_dir, self.uid, self.gid)
            # now do install
            arguments = [
                    util_which.which_ceph_mon.path,
                    "--mkfs",
                    "-i",
                    service_name,
                    "--monmap",
                    path_monmap,
                    '--keyring',
                    key_path
                    ]
            output = self._execute(arguments)
            if output["retcode"] != 0:
                raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                    " ".join(arguments),
                    output["retcode"],
                    output["stdout"],
                    output["stderr"]
                    ))
            # check keyring created:
            path_mon_key = os.path.join(path_mon_dir, "keyring")
            if not os.path.isfile(path_mon_key):
                raise Error("Failed to create '%s'" % (path_mon_key))
            # Now start the service
            arguments = {
                'identifier' : service_name,
                'service' : "ceph-mon",
            }
            self.init_system.restart(**arguments)
            self.init_system.on_boot_enable(**arguments)
            self._create_check_retry(**kwargs)
            open(path_done_file, 'a').close()
        finally:
            log.info("Destroy temp directory %s" %(tmpd))
            shutil.rmtree(tmpd)
        return True


    def destroy(self, **kwargs):
        """
        Destroy a mon node

        Args:
            **kwargs: Arbitrary keyword arguments.
                mon_name
                    set the mon you are destroying.
                cluster_uuid
                    Set the cluster UUID. Defaults to value found in ceph
                    config file.
                cluster_name
                    Set the cluster name. Defaults to "ceph".
        """
        service_name = kwargs.get("mon_name")
        if service_name is None:
            raise Error("Service name for mon is not specified as 'mon_name'")
        if util_which.which_ceph_mon.path is None:
            raise Error("Could not find executable 'ceph-mon'")

        #Validate not in core mon list as this fails with a nasty error
        if self.mon_is(**kwargs):
            msg = """mon '{service_name}' is still in the the ceph configuration so failing to remove""".format(
                service_name=service_name)
            log.error(msg)
            raise Error(msg)

        # Check the mon is local
        service_dir = "{cluster}-{service}".format(
            cluster=self.model.cluster_name,
            service=service_name
            )
        path = os.path.join(constants._path_ceph_lib_mon, service_dir)
        if not os.path.isdir(path):
            return True
        # Now stop and disable the service
        arguments = {
            'identifier' : service_name,
            'service' : "ceph-mon",
        }
        if self.init_system.is_running(**arguments):
            self.init_system.stop(**arguments)
        self.init_system.on_boot_disable(**arguments)
        log.debug("removing mon path {path}".format(path=path))
        try:
            shutil.rmtree(path)
        finally:
            # Now we can safely remove the mon from the mon map
            # Doing this on anouther node can lead to the mon restarting to fast
            # particulalry under systemd where it autorestarts, this consumes
            # load and systemd prevents starting the service for 30m.
            mon_ops = ops_mon.ops_mon(self.model)
            mon_ops.monmap_remove(service_name)
        return True


    def active(self, **kwargs):
        """
        Is mon deamon running
        """
        service_name = kwargs.get("mon_name")
        if service_name is None:
            raise Error("Service name for mon is not specified as 'mon_name'")
        arguments = {
                'identifier' : service_name,
                'service' : "ceph-mon",
            }
        init_system = service.init_system(init_type=self.model.init)
        return init_system.is_running(**arguments)


    def list(self, **kwargs):
        """
        Update model of local mons
        """
        subdirs = []
        for dir_entry in os.listdir(constants._path_ceph_lib_mon):
            path = os.path.join(constants._path_ceph_lib_mon, dir_entry)
            if not os.path.isdir(path):
                continue
            subdirs.append(dir_entry)
        mon_services = {}
        for directory in subdirs:
            dir_split = directory.split('-')
            if len(dir_split) == 1:
                log.warning("mon directory is invalid")
                continue
            head = dir_split[0]
            tail = '-'.join(dir_split[1:])
            if not head in mon_services:
                mon_services[head] = [tail]
            else:
                mon_services[head].append(tail)
        self.model.mon_local_services = mon_services
        return self.model.mon_local_services


class mod_user_root(mon_implementation_base):
    def __init__(self, mdl):
        mon_implementation_base.__init__(self, mdl)
        self.uid = 0
        self.gid = 0


class mod_user_ceph(mon_implementation_base):
    def __init__(self, mdl):
        mon_implementation_base.__init__(self, mdl)
        pwd_struct = pwd.getpwnam("ceph")
        self.uid = pwd_struct.pw_uid
        self.gid = pwd_struct.pw_gid


    def _execute(self,arguments):
        prefix = [
            "sudo",
            "-u",
            "ceph"
            ]
        return utils.execute_local_command(prefix + arguments)


class mon_facard(object):
    def __init__(self, model, **kwargs):
        self.model = model
        self._clear_implementation()
        u = mdl_updater.model_updater(self.model)
        u.ceph_version_refresh()
        q = mdl_query.mdl_query(self.model)
        self.ceph_daemon_user = q.ceph_daemon_user()


    def _clear_implementation(self):
        self._ceph_daemon_user = None
        self._monImp = None


    @Property
    def ceph_daemon_user():
        doc = "key_type"

        def fget(self):
            return self._ceph_daemon_user


        def fset(self, user):
            if user is None:
                self._clear_implementation()
            implementation = None
            if user == "root":
                implementation = mod_user_root(self.model)
            if user == "ceph":
                implementation = mod_user_ceph(self.model)
            if implementation is None:
                raise Error("Invalid ceph_daemon_user")
            self._monImp = implementation
            self._ceph_daemon_user = user
            return self._ceph_daemon_user


        def fdel(self):
            self._clear_implementation()


        return locals()


    def create(self, **kwargs):
        """
        Create mon
        """
        if self._monImp is None:
            raise Error("Programming error: key type unset")
        return self._monImp.create(**kwargs)


    def destroy(self, **kwargs):
        """
        Destroy mon
        """
        if self._monImp is None:
            raise Error("Programming error: key type unset")
        return self._monImp.destroy(**kwargs)


    def quorum(self, **kwargs):
        if self._monImp is None:
            raise Error("Programming error: key type unset")
        return self._monImp.quorum(**kwargs)


    def status(self, **kwargs):
        if self._monImp is None:
            raise Error("Programming error: key type unset")
        return self._monImp.status(**kwargs)


    def is_mon(self, **kwargs):
        if self._monImp is None:
            raise Error("Programming error: key type unset")
        return self._monImp.mon_is(**kwargs)


    def active(self, **kwargs):
        if self._monImp is None:
            raise Error("Programming error: key type unset")
        return self._monImp.active(**kwargs)


    def list(self, **kwargs):
        if self._monImp is None:
            raise Error("Programming error: key type unset")
        return self._monImp.list(**kwargs)


def _update_mon_model(model):
    u = mdl_updater.model_updater(model)
    u.defaults_hostname()
    u.defaults_refresh()
    u.load_confg(model.cluster_name)
    u.mon_members_refresh()


def mon_is(**kwargs):
    """
    Is this a mon node

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    mdl = model.model(**kwargs)
    try:
        _update_mon_model(mdl)
    except ErrorNotMon:
        return False
    ctrl_mon = mon_facard(mdl, **kwargs)
    return ctrl_mon.is_mon()


def mon_status(**kwargs):
    """
    Get status from mon deamon

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    mdl = model.model(**kwargs)
    _update_mon_model(mdl)
    ctrl_mon = mon_facard(mdl, **kwargs)
    return ctrl_mon.status(**kwargs)


def mon_quorum(**kwargs):
    """
    Is mon deamon in quorum

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    mdl = model.model(**kwargs)
    _update_mon_model(mdl)
    ctrl_mon = mon_facard(mdl, **kwargs)
    return ctrl_mon.quorum(**kwargs)


def mon_active(**kwargs):
    """
    Is mon deamon running

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    mdl = model.model(**kwargs)
    _update_mon_model(mdl)
    ctrl_mon = mon_facard(mdl, **kwargs)
    return ctrl_mon.active(**kwargs)


def mon_create(**kwargs):
    """
    Create a mon node

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    mdl = model.model(**kwargs)
    _update_mon_model(mdl)
    ctrl_mon = mon_facard(mdl, **kwargs)
    return ctrl_mon.create(**kwargs)


def mon_destroy(**kwargs):
    """
    Destroy a mon node

    Args:
        **kwargs: Arbitrary keyword arguments.
            mon_name
                set the mon you are destroying.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    mdl = model.model(**kwargs)
    _update_mon_model(mdl)
    ctrl_mon = mon_facard(mdl, **kwargs)
    return ctrl_mon.destroy(**kwargs)


def mon_list(**kwargs):
    """
    Create a mon node

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    mdl = model.model(**kwargs)
    _update_mon_model(mdl)
    ctrl_mon = mon_facard(mdl, **kwargs)
    return ctrl_mon.list()
