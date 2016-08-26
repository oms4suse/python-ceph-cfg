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


class ops_cluster(object):
    """
    Operations to be done on the pools.
    """
    def __init__(self, model):
        self.model = model
        self.connection = remote_connection.connection(self.model)


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
        self.model.cluster_status = json.loads(output["stdout"].strip())
