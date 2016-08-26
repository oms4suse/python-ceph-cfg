# Import Python Libs
from __future__ import absolute_import
import logging
import shlex


# Local imports
from . import util_which
from . import remote_connection
from . import utils
from . import keyring
from . import mdl_query


log = logging.getLogger(__name__)


class Error(Exception):
    """
    Error
    """

    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [str(a) for a in self.args])



class ops_auth(object):
    """
    Operations to be done on the pools.
    """
    def __init__(self, model):
        self.model = model
        self.connection = remote_connection.connection(self.model)


    def auth_list(self):
        prefix_arguments = [
            util_which.which_ceph.path
        ]
        postfix_arguments = [
            "auth",
            "list"
            ]
        connection_arguments = self.connection.arguments_get()
        arguments = prefix_arguments + connection_arguments + postfix_arguments
        output = utils.execute_local_command(arguments)
        if output["retcode"] != 0:
            raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                        " ".join(arguments),
                        output["retcode"],
                        output["stdout"],
                        output["stderr"])
                        )
        auth_list_out = {}
        section = {}
        for line in output["stdout"].split('\n'):
            if len(line) == 0:
                continue
            if line[0] != '\t':
                prev_sec_name = section.get("name")
                if prev_sec_name is not None:
                    auth_list_out[prev_sec_name] = section
                section = { "name" : line }
                continue
            tokenised_line = shlex.split(line)
            if len(tokenised_line) == 0:
                continue
            if tokenised_line[0] == 'key:':
                section['key'] = tokenised_line[1]
            if tokenised_line[0] == 'caps:':
                if not 'caps' in section:
                    section['caps'] = []
                cap_details = tokenised_line[1:]
                section["caps"].append(cap_details)


        prev_sec_name = section.get("name")
        if prev_sec_name is not None:
            auth_list_out[prev_sec_name] = section
        self.model.auth_list = auth_list_out


    def auth_add(self, keyring_type):
        """
        Authorise keyring
        """
        keyringobj = keyring.keyring_facard(self.model)
        keyringobj.key_type = keyring_type


        if not keyringobj.present():
            raise Error("rgw keyring not found")
        q = mdl_query.mdl_query(self.model)
        if q.mon_is() and q.mon_quorum() is False:
            raise Error("mon daemon is not in quorum")
        prefix_arguments = [
            util_which.which_ceph.path
        ]
        postfix_arguments = [
            "auth",
            "import",
            "-i",
            keyringobj.keyring_path_get()
            ]
        connection_arguments = self.connection.arguments_get()
        arguments = prefix_arguments + connection_arguments + postfix_arguments
        output = utils.execute_local_command(arguments)
        if output["retcode"] != 0:
            raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                        " ".join(arguments),
                        output["retcode"],
                        output["stdout"],
                        output["stderr"])
                        )
        return True


    def auth_del(self, keyring_type):
        """
        Remove Authorised keyring
        """
        keyringobj = keyring.keyring_facard(self.model)
        keyringobj.key_type = keyring_type
        q = mdl_query.mdl_query(self.model)
        if q.mon_is() and q.mon_quorum() is False:
            raise Error("mon daemon is not in quorum")
        prefix_arguments = [
            util_which.which_ceph.path
        ]
        postfix_arguments = [
            "auth",
            "del",
            keyringobj.keyring_identity_get()
            ]
        connection_arguments = self.connection.arguments_get()
        arguments = prefix_arguments + connection_arguments + postfix_arguments
        output = utils.execute_local_command(arguments)
        if output["retcode"] != 0:
            raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                        " ".join(arguments),
                        output["retcode"],
                        output["stdout"],
                        output["stderr"])
                        )
        return True
