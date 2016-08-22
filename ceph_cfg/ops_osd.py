# Import Python Libs
from __future__ import absolute_import
import logging

# Local imports
from . import model
from . import mdl_updater
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


class ops_osd(object):
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


    def reweight(self, osd, weight):
        prefix_arguments = [
            util_which.which_ceph.path
        ]
        postfix_arguments = [
            'osd',
            'reweight',
            str(osd),
            str(weight)
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


def reweight(**kwargs):
    """
    Reweight an OSD, or OSD's on node.

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_name : Set the cluster name. Defaults to "ceph".
            cluster_uuid : Set the cluster date will be added too. Defaults to
                the value found in local config.
            osd_number : OSD number to reweight. Defaults to all OSD's on node.
            osd_uuid : OSD uuid to reweight. Defaults to all OSD's on node.
            weight : The new weight for the node. weight is a float, and must be
                in the range 0 to 1.

    Note:
        Setting the weight to 0 will drain an OSD.
    """
    mdl = model.model(**kwargs)
    u = mdl_updater.model_updater(mdl)
    u.symlinks_refresh()
    u.defaults_refresh()
    u.partitions_all_refresh()
    u.discover_partitions_refresh()
    u.hostname_refresh()
    u.defaults_refresh()
    u.load_confg(mdl.cluster_name)
    u.mon_members_refresh()
    # Validate input
    osd_number_input = kwargs.get("osd_number")
    #osd_uuid = kwargs.get("osd_uuid")
    weight = kwargs.get("weight")
    if weight is None:
        raise Error("weight is not specified")
    if osd_number_input is None:
        pass
    osd_ops = ops_osd(mdl)
    osd_ops.reweight(osd_number_input, weight)
