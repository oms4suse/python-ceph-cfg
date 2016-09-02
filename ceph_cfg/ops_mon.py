# Import Python Libs
from __future__ import absolute_import
import logging

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


class ops_mon(object):
    """
    Since presentation should be clean to the end user
    We abstract such functiosn in this class.
    """
    def __init__(self, model):
        self.model = model
        self.connection = remote_connection.connection(self.model)


    def _osd_local(self):
        local_osd = []
        osd_list_existing = self.model.discovered_osd.get(self.cluster_uuid)
        if osd_list_existing is not None:
            for osd_existing in osd_list_existing:
                whoami = osd_existing.get("whoami")
                if whoami is not None:
                    local_osd.append(int(whoami))
        return local_osd


    def monmap_remove(self, mon_name):
        prefix_arguments = [
            util_which.which_ceph.path
        ]
        postfix_arguments = [
            'mon',
            'remove',
            str(mon_name)
        ]
        connection_arguments = self.connection.arguments_get()
        arguments = prefix_arguments + connection_arguments + postfix_arguments
        output = utils.execute_local_command(arguments)
        # Outputs to stderr information
        log.debug(output["stderr"])
        # Seems this command allways gives rc of 22
        # See http://tracker.ceph.com/issues/17190
        if not output["retcode"] in [0, 22]:
            msg = "Failed executing '{cmdline}' Error rc={retcode}, stdout={stdout} stderr={stderr}".format(
                cmdline=" ".join(arguments),
                retcode=output["retcode"],
                stdout=output["stdout"],
                stderr=output["stderr"])
            log.error(msg)
            raise Error(msg)
        return True
