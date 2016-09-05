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


    def _df_node_to_osd_dict(self, node):
        node_type = node.get("type")
        if node_type != "osd":
            return None
        osd_id = node.get("id")
        osd_name = node.get("name")
        osd_weight_crush = node.get("crush_weight")
        osd_weight = node.get("reweight")
        osd_kb_total = node.get("kb")
        osd_kb_used = node.get("kb_used")
        osd_kb_avail = node.get("kb_avail")
        osd_pgs = node.get("pgs")
        osd_utilization = node.get("utilization")
        return {
            "id" : osd_id,
            "name" : osd_name,
            "weight_crush" : osd_weight_crush,
            "weight" : osd_weight,
            "kb_total" : osd_kb_total,
            "kb_used" : osd_kb_used,
            "kb_avail" : osd_kb_avail,
            "pgs" : osd_pgs,
            "utilization" : osd_utilization
        }


    def df(self):
        prefix_arguments = [
            util_which.which_ceph.path
        ]
        postfix_arguments = [
            'osd',
            'df',
            '-f',
            'json'
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
        df_dict = json.loads(output["stdout"])
        nodes_list = df_dict.get("nodes")
        osd_details = {}
        if not nodes_list is None:
            for node in nodes_list:
                osd_dict = self._df_node_to_osd_dict(node)
                if not osd_dict is None:
                    osd_details[osd_dict.get("id")] = osd_dict

        summary_raw = df_dict.get("summary")
        summary_model = {}
        if not summary_raw is None:
            summary_model["kb_total"] = summary_raw.get("total_kb")
            summary_model["kb_used"] = summary_raw.get("kb_used")
            summary_model["kb_avail"] = summary_raw.get("total_kb_avail")
            summary_model["utilization_average"] = summary_raw.get("average_utilization")
        stored_model = {
            'osd' : osd_details,
            'summary' : summary_model
        }
        self.model.cluster_df = stored_model
        return self.model.cluster_df
