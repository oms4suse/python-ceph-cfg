# This module is to update the model with remote commands.

# Import Python Libs
from __future__ import absolute_import
import logging
import os
import json

# Local imports
from . import keyring
from . import utils
from . import util_which
from . import constants


log = logging.getLogger(__name__)


class Error(Exception):
    """
    Error
    """

    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [str(a) for a in self.args])


class connection():
    """
    Basic connection tool.
    """
    def __init__(self, model):
        self.model = model


    def arguments_get(self):
        if not self.has_connected():
            self.connect()
        if self.has_connected():
            return [
                    '--connect-timeout',
                    '%s' % (constants.ceph_remote_call_timeout),
                    "--keyring",
                    self.model.connection.keyring_path,
                    "--name",
                    self.model.connection.keyring_identity,
                ]
        raise Error("Failed to connect to cluster")


    def has_connected(self):
        if self.model.connection.keyring_type is None:
            return False
        if self.model.connection.keyring_path is None:
            return False
        if self.model.connection.keyring_identity is None:
            return False
        return True


    def connect(self):
        if self.has_connected() is True:
            return True
        keyring_obj = keyring.keyring_facard(self.model)
        for keytype in ["admin", "osd", "mds", "rgw", "mon"]:
            log.debug("Trying keyring:%s" % (keytype))
            keyring_obj.key_type = keytype
            keyring_path = keyring_obj.keyring_path_get()
            if not os.path.isfile(keyring_path):
                log.debug("Skipping keyring %s" % (keyring_path))
                continue
            keyring_identity = keyring_obj.keyring_identity_get()
            arguments = [
                util_which.which_ceph.path,
                '--connect-timeout',
                '%s' % (constants.ceph_remote_call_timeout),
                "--keyring",
                keyring_path,
                "--name",
                keyring_identity,
                "-f",
                "json-pretty",
                "status"
            ]
            output = utils.execute_local_command(arguments)
            if output["retcode"] != 0:
                continue
            self.model.cluster_status = json.loads(output["stdout"].strip())
            self.model.connection.keyring_type = keytype
            self.model.connection.keyring_path = keyring_path
            self.model.connection.keyring_identity = keyring_identity
            return True
        return False
