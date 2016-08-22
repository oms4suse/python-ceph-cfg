# This module is to update the model with remote commands.

# Import Python Libs
from __future__ import absolute_import
import logging
import os
import json
import shlex

# Local imports
from . import keyring
from . import utils
from . import mdl_query
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


class model_updater_remote():
    """
    Basic model updator retrives data and adds to model
    """
    def __init__(self, model):
        self.model = model
        self.keyring_type = None
        self.keyring_path = None
        self.keyring_identity = None


    def connection_arguments_get(self):
        if self.keyring_type != None:
            return [
                    '--connect-timeout',
                    '%s' % (constants.ceph_remote_call_timeout),
                    "--keyring",
                    self.keyring_path,
                    "--name",
                    self.keyring_identity,
                ]
        raise Error("No keytype selected")


    def connect(self):
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
            self.keyring_type = keytype
            self.keyring_path = keyring_path
            self.keyring_identity = keyring_identity
            return True
        return False


    def status_refresh(self):
        """
        Get the cluster status

        This is not normally needed as connect method has updated this information
        """
        prefix_arguments = [
            util_which.which_ceph.path
        ]
        postfix_arguments = [
            "-f",
            "json-pretty",
            "status"
        ]
        connection_arguments = self.connection_arguments_get()
        arguments = prefix_arguments + connection_arguments + postfix_arguments
        output = utils.execute_local_command(arguments)

        if output["retcode"] != 0:
            raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                        " ".join(arguments),
                        output["retcode"],
                        output["stdout"],
                        output["stderr"])
                        )
        self.model.cluster_status = json.loads(output["stdout"].strip())


    def auth_list(self):
        prefix_arguments = [
            util_which.which_ceph.path
        ]
        postfix_arguments = [
            "auth",
            "list"
            ]
        connection_arguments = self.connection_arguments_get()
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
        connection_arguments = self.connection_arguments_get()
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
        connection_arguments = self.connection_arguments_get()
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
        connection_arguments = self.connection_arguments_get()
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
        connection_arguments = self.connection_arguments_get()
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
        connection_arguments = self.connection_arguments_get()
        arguments = prefix_arguments + connection_arguments + postfix_arguments
        output = utils.execute_local_command(arguments)
        if output["retcode"] != 0:
            raise Error("Failed executing '%s' Error rc=%s, stdout=%s stderr=%s" % (
                        " ".join(arguments),
                        output["retcode"],
                        output["stdout"],
                        output["stderr"]))
        return True
