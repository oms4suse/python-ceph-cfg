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



class ops_cephfs(object):
    """
    Operations to be done on the pools.
    """
    def __init__(self, model):
        self.model = model
        self.connection = remote_connection.connection(self.model)


    def cephfs_list(self):
        prefix_arguments = [
            util_which.which_ceph.path
        ]
        postfix_arguments = [
            "-f",
            "json",
            "fs",
            "ls"
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
        failed_list = []
        for item in json.loads(output["stdout"].strip()):
            cephfs_name = item.get("name")
            cephfs_pool_metadata = item.get("metadata_pool")
            cephfs_pool_metadata_id = item.get("metadata_pool_id")
            cephfs_pool_data_ids = item.get("data_pool_ids")
            cephfs_pool_data = item.get("data_pools")
            if len(cephfs_pool_data_ids) != len(cephfs_pool_data):
                msg = "Failed reading cephfs datapool for '{cephfs_name}' ".format(cephfs_name=cephfs_name)
                log.error(msg)
                failed_list.add(cephfs_name)
                continue
            if cephfs_name in details:
                msg = "Failed reading cephfs due to duplicate for '{cephfs_name}' ".format(cephfs_name=cephfs_name)
                log.error(msg)
                failed_list.add(cephfs_name)
                continue
            pool_data = []
            for index in range(len(cephfs_pool_data_ids)):
                pool_data.append([cephfs_pool_data_ids[index], cephfs_pool_data[index]])
            details[cephfs_name] = {
                "metadata" : [cephfs_pool_metadata_id,cephfs_pool_metadata],
                "data" : pool_data
                }
        if len(failed_list) > 0:
            error_list = ", ".join(failed_list)
            msg = "Failed reading cephfs list : " + error_list
            raise Error(msg)
        self.model.cephfs_list = details


    def cephfs_add(self, cephfs_name, **kwargs):
        if cephfs_name in self.model.cephfs_list.keys():
            return True
        pool_metadata = kwargs.get("pool_metadata")
        if pool_metadata is None:
            msg = "Did not specifiy 'pool_metadata'"
            log.error(msg)
            raise Error(msg)
        pool_data = kwargs.get("pool_data")
        if pool_data is None:
            msg = "Did not specifiy 'pool_data'"
            log.error(msg)
            raise Error(msg)
        if not pool_metadata in self.model.pool_list.keys():
            msg = "Invalid pool set for pool_metadata '{pool_metadata}'".format(pool_metadata)
            log.error(msg)
            raise Error(msg)
        if not pool_data in self.model.pool_list.keys():
            msg = "Invalid pool set for pool_data '{pool_data}'".format(pool_data)
            log.error(msg)
            raise Error(msg)
        prefix_arguments = [
            util_which.which_ceph.path
        ]
        postfix_arguments = [
            'fs',
            'new',
            cephfs_name,
            pool_metadata,
            pool_data
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


    def cephfs_del(self, cephfs_name, **kwargs):
        if not cephfs_name in self.model.cephfs_list.keys():
            log.debug("No action needed as '{cephfs_name}' does not exist".format(cephfs_name=cephfs_name))
            return True
        prefix_arguments = [
            util_which.which_ceph.path
        ]
        postfix_arguments = [
            'fs',
            'rm',
            cephfs_name
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
