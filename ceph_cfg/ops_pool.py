# Import Python Libs
from __future__ import absolute_import
import logging
import json

# Local imports
from . import util_which
from . import remote_connection
from . import utils

log = logging.getLogger(__name__)


class Error(Exception):
    """
    Error
    """

    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [str(a) for a in self.args])



class ops_pool(object):
    """
    Operations to be done on the pools.
    """
    def __init__(self, model):
        self.model = model
        self.connection = remote_connection.connection(self.model)


    def pool_list(self):
        prefix_arguments = [
            util_which.which_ceph.path
        ]
        postfix_arguments = [
            "-f",
            "json",
            "osd",
            "lspools"
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
        details = {}
        for item in json.loads(output["stdout"].strip()):
            pool_num = item.get("poolnum")
            pool_name = item.get("poolname")
            details[pool_name] = {"poolnum" : pool_num }
        self.model.pool_list = details


    def _pool_adder(self, name, **kwargs):
        pg_num = kwargs.get("pg_num", 8)
        pgp_num = kwargs.get("pgp_num", pg_num)
        pool_type = kwargs.get("pool_type")
        er_profile = kwargs.get("erasure_code_profile")
        crush_ruleset_name = kwargs.get("crush_ruleset")
        prefix_arguments = [
            util_which.which_ceph.path
        ]
        postfix_arguments = [
            'osd',
            'pool',
            'create',
            name,
            str(pg_num)
            ]
        connection_arguments = self.connection.arguments_get()
        arguments = prefix_arguments + connection_arguments + postfix_arguments
        if pgp_num is not None:
            arguments.append(str(pgp_num))
        if pool_type == "replicated":
            arguments.append("replicated")
        if pool_type == "erasure":
            arguments.append("erasure")
            arguments.append("erasure-code-profile=%s" % (er_profile))
        if crush_ruleset_name is not None:
            arguments.append(crush_ruleset_name)
        output = utils.execute_local_command(arguments)
        if output["retcode"] != 0:
            raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                        " ".join(arguments),
                        output["retcode"],
                        output["stdout"],
                        output["stderr"]))
        return True


    def pool_add(self, name, **kwargs):
        if not name in self.model.pool_list.keys():
            return self._pool_adder(name, **kwargs)
        return True


    def pool_del(self, name):
        if not name in self.model.pool_list.keys():
            return True
        prefix_arguments = [
            util_which.which_ceph.path
        ]
        postfix_arguments = [
            'osd',
            'pool',
            'delete',
            name,
            name,
            '--yes-i-really-really-mean-it'
            ]
        connection_arguments = self.connection.arguments_get()
        arguments = prefix_arguments + connection_arguments + postfix_arguments
        output = utils.execute_local_command(arguments)
        if output["retcode"] != 0:
            raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                        " ".join(arguments),
                        output["retcode"],
                        output["stdout"],
                        output["stderr"]))
        return True
