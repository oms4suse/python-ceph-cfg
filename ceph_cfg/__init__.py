# Import Python Libs
from __future__ import absolute_import
import logging
import stat
import os.path
import os
import subprocess

# local modules
from . import util_which
from . import utils
from . import model
from . import mdl_updater
from . import presenter
from . import mdl_query
from . import osd
from . import mon
from . import rgw
from . import mds
from . import purger
from . import ops_pool
from . import ops_cephfs
from . import ops_auth
from . import ops_cluster
from . import keyring_use
from . import ops_osd

log = logging.getLogger(__name__)


class Error(Exception):
    """
    Error
    """

    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [str(a) for a in self.args])


def partition_list():
    '''
    List partitions by disk
    '''
    m = model.model()
    u = mdl_updater.model_updater(m)
    u.symlinks_refresh()
    u.partitions_all_refresh()
    p = presenter.mdl_presentor(m)
    return p.partitions_all()

def partition_list_osd():
    '''
    List all OSD data partitions by partition
    '''
    m = model.model()
    u = mdl_updater.model_updater(m)
    u.symlinks_refresh()
    u.partitions_all_refresh()
    u.discover_partitions_refresh()
    p = presenter.mdl_presentor(m)
    return p.discover_osd_partitions()


def partition_list_journal():
    '''
    List all OSD journal partitions by partition
    '''
    m = model.model()
    u = mdl_updater.model_updater(m)
    u.symlinks_refresh()
    u.partitions_all_refresh()
    u.discover_partitions_refresh()
    p = presenter.mdl_presentor(m)
    return p.discover_journal_partitions()

def osd_discover():
    """
    List all OSD by cluster
    """
    m = model.model()
    u = mdl_updater.model_updater(m)

    u.symlinks_refresh()
    u.partitions_all_refresh()
    u.discover_partitions_refresh()
    p = presenter.mdl_presentor(m)
    return p.discover_osd()


def partition_is(dev):
    """
    Check whether a given device path is a partition or a full disk.

    Args:
        dev : Block device to test.
    """
    mdl = model.model()
    osdc = osd.osd_ctrl(mdl)
    return osdc.is_partition(dev)


def _update_partition(action, dev, description):
    # try to make sure the kernel refreshes the table.  note
    # that if this gets ebusy, we are probably racing with
    # udev because it already updated it.. ignore failure here.

    # On RHEL and CentOS distros, calling partprobe forces a reboot of the
    # server. Since we are not resizing partitons so we rely on calling
    # partx

    utils.execute_local_command(
        [
             util_which.which_partprobe.path,
             dev,
        ],
    )



def zap(dev = None, **kwargs):
    """
    Destroy the partition table and content of a given disk.
    """
    if dev is not None:
        log.warning("Depricated use of function, use kwargs")
    dev = kwargs.get("dev", dev)
    if dev == None:
        raise Error('Cannot find', dev)
    if not os.path.exists(dev):
        raise Error('Cannot find', dev)
    dmode = os.stat(dev).st_mode
    mdl = model.model(**kwargs)
    osdc = osd.osd_ctrl(mdl)
    if not stat.S_ISBLK(dmode) or osdc.is_partition(dev):
        raise Error('not full block device; cannot zap', dev)
    try:
        log.debug('Zapping partition table on %s', dev)

        # try to wipe out any GPT partition table backups.  sgdisk
        # isn't too thorough.
        lba_size = 4096
        size = 33 * lba_size
        with open(dev, 'wb') as dev_file:
            dev_file.seek(-size, os.SEEK_END)
            dev_file.write(size*'\0')

        utils.execute_local_command(
            [
                util_which.which_sgdisk.path,
                '--zap-all',
                '--',
                dev,
            ],
        )
        utils.execute_local_command(
            [
                util_which.which_sgdisk.path,
                '--clear',
                '--mbrtogpt',
                '--',
                dev,
            ],
        )


        _update_partition('-d', dev, 'zapped')
    except subprocess.CalledProcessError as e:
        raise Error(e)
    return True


def osd_prepare(**kwargs):
    """
    prepare an OSD

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID.
            journal_dev : Set the journal device. defaults to osd_dev.
            cluster_name : Set the cluster name. Defaults to "ceph".
            cluster_uuid : Set the cluster date will be added too. Defaults to
                the value found in local config.
            osd_fs_type : Set the file system to store OSD data with. Defaults
                to "xfs".
            osd_uuid : Set the OSD data UUID. If set will return if OSD with
                data UUID already exists.
            journal_uuid : Set the OSD journal UUID. If set will return if OSD
                with journal UUID already exists.
    """
    return osd.osd_prepare(**kwargs)


def osd_activate(**kwargs):
    """
    Activate an OSD

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID.
            journal_dev : Set the journal device. defaults to osd_dev.
            cluster_name : Set the cluster name. Defaults to "ceph".
            cluster_uuid : Set the cluster date will be added too. Defaults to
                the value found in local config.
            osd_fs_type : Set the file system to store OSD data with. Defaults
                to "xfs".
            osd_uuid : Set the OSD data UUID. If set will return if OSD with
                data UUID already exists.
            journal_uuid : Set the OSD journal UUID. If set will return if OSD
                with journal UUID already exists.
    """
    return osd.osd_activate(**kwargs)


def osd_reweight(**kwargs):
    """
    Reweight an OSD, or OSD's on node.

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_name : Set the cluster name. Defaults to "ceph".
            cluster_uuid : Set the cluster date will be added too. Defaults to
                the value found in local config.
            osd_number : OSD number to reweight.
            weight : The new weight for the node. weight is a float, and must be
                in the range 0 to 1.

    Note:
        Setting the weight to 0 will drain an OSD.
    """
    return ops_osd.reweight(**kwargs)


def keyring_create(**kwargs):
    """
    Create keyring for cluster

    Args:
        **kwargs: Arbitrary keyword arguments.
            keyring_type : Required parameter. Can be set to: admin, mon, osd,
                rgw, mds.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    return keyring_use.keyring_create_type(**kwargs)


def keyring_save(**kwargs):
    """
    Create save keyring locally

    Args:
        **kwargs: Arbitrary keyword arguments.
            keyring_type: Required parameter. Can be set to: admin, mon, osd,
                rgw, mds
            secret: The shared secret in the key
            key_content : The complete key including capabilities.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    return keyring_use.keyring_save_type(**kwargs)


def keyring_purge(**kwargs):
    """
    Delete keyring for cluster

    Args:
        **kwargs: Arbitrary keyword arguments.
            keyring_type : Required parameter. Can be set to: admin, mon, osd,
                rgw, mds
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    return keyring_use.keyring_purge_type(**kwargs)


def keyring_present(**kwargs):
    """
    Is keyring on disk

    Args:
        **kwargs: Arbitrary keyword arguments.
            keyring_type : Required parameter. Can be set to: admin, mon, osd,
                rgw, mds.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    return keyring_use.keyring_present_type(**kwargs)


def keyring_auth_add(**kwargs):
    """
    Add keyring to authorised list

    Args:
        **kwargs: Arbitrary keyword arguments.
            keyring_type : Required parameter. Can be set to: admin, mon, osd,
                rgw, mds.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    return keyring_use.keyring_auth_add_type(**kwargs)


def keyring_auth_del(**kwargs):
    """
    Remove keyring from authorised list

    Args:
        **kwargs: Arbitrary keyword arguments.
            keyring_type
                Required parameter. Can be set to: admin, mon, osd, rgw, mds
            cluster_uuid
                Set the cluster UUID. Defaults to value found in ceph config file.
            cluster_name
                Set the cluster name. Defaults to "ceph".
    """
    return keyring_use.keyring_auth_del_type(**kwargs)


def keyring_admin_create(**kwargs):
    """
    Create admin keyring for cluster

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid
                Set the cluster UUID. Defaults to value found in ceph config file.
            cluster_name
                Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "admin"
    return keyring_create(**params)


def keyring_admin_save(key_content=None, **kwargs):
    """
    Write admin keyring for cluster

    Args:
        **kwargs: Arbitrary keyword arguments.
            secret: The shared secret in the key
            key_content : The complete key including capabilities.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "admin"
    if key_content is None:
        return keyring_save(**params)
    log.warning("keyring_admin_save using legacy argument call")
    params["key_content"] = str(key_content)
    return keyring_save(**params)


def keyring_admin_purge(**kwargs):
    """
    Delete Mon keyring for cluster

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "admin"
    return keyring_purge(**params)


def keyring_mon_create(**kwargs):
    """
    Create mon keyring for cluster

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "mon"
    return keyring_create(**params)


def keyring_mon_save(key_content=None, **kwargs):
    """
    Write mon keyring for cluster

    Args:
        key_content : The complete key including capabilities.
        **kwargs: Arbitrary keyword arguments.
            secret: The shared secret in the key
            key_content : The complete key including capabilities.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "mon"
    if key_content is None:
        return keyring_save(**params)
    log.warning("keyring_admin_save using legacy argument call")
    params["key_content"] = str(key_content)
    return keyring_save(**params)


def keyring_mon_purge(**kwargs):
    """
    Delete mon keyring for cluster

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "mon"
    return keyring_purge(**params)


def keyring_osd_create(**kwargs):
    """
    Create osd keyring for cluster

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "osd"
    return keyring_create(**params)


def keyring_osd_save(key_content=None, **kwargs):
    """
    Write osd keyring for cluster

    Args:
        key_content : The complete key including capabilities.
        **kwargs: Arbitrary keyword arguments.
            secret: The shared secret in the key
            key_content : The complete key including capabilities.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "osd"
    if key_content is None:
        return keyring_save(**params)
    log.warning("keyring_admin_save using legacy argument call")
    params["key_content"] = str(key_content)
    return keyring_save(**params)


def keyring_osd_auth_add(**kwargs):
    """
    Add osd keyring to cluster

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "osd"
    return keyring_auth_add(**params)


def keyring_osd_auth_del(**kwargs):
    """
    Remove osd keyring from cluster

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "osd"
    return keyring_auth_del(**params)


def keyring_osd_purge(**kwargs):
    """
    Remove osd keyring from node

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "osd"
    return keyring_purge(**params)


def keyring_mds_create(**kwargs):
    """
    Create mds keyring for cluster

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "mds"
    return keyring_create(**params)


def keyring_mds_save(key_content=None, **kwargs):
    """
    Write mds bootstrap keyring for cluster to node

    Args:
        key_content : The complete key including capabilities.
        **kwargs: Arbitrary keyword arguments.
            secret: The shared secret in the key
            key_content : The complete key including capabilities.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "mds"
    if key_content is None:
        return keyring_save(**params)
    log.warning("keyring_admin_save using legacy argument call")
    params["key_content"] = str(key_content)
    return keyring_save(**params)


def keyring_mds_auth_add(**kwargs):
    """
    Add mds bootstrap keyring to cluster.

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "mds"
    return keyring_auth_add(**params)


def keyring_mds_auth_del(**kwargs):
    """
    Remove mds bootstrap keyring from cluster.

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "mds"
    return keyring_auth_del(**params)


def keyring_mds_purge(**kwargs):
    """
    Delete mds keyring for cluster from node.

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "mds"
    return keyring_purge(**params)


def keyring_rgw_create(**kwargs):
    """
    Create rgw bootstrap keyring for cluster.

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "rgw"
    return keyring_create(**params)


def keyring_rgw_save(key_content=None, **kwargs):
    """
    Write rgw bootstrap keyring for cluster to node

    Args:
        key_content : The complete key including capabilities.
        **kwargs: Arbitrary keyword arguments.
            secret: The shared secret in the key
            key_content : The complete key including capabilities.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "rgw"
    if key_content is None:
        return keyring_save(**params)
    log.warning("keyring_admin_save using legacy argument call")
    params["key_content"] = str(key_content)
    return keyring_save(**params)


def keyring_rgw_auth_add(**kwargs):
    """
    Add rgw bootstrap keyring from cluster.

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "rgw"
    return keyring_auth_add(**params)


def keyring_rgw_auth_del(**kwargs):
    """
    Remove rgw bootstrap keyring from cluster.

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "rgw"
    return keyring_auth_del(**params)


def keyring_rgw_purge(**kwargs):
    """
    Delete mds keyring for cluster from node.

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    params = dict(kwargs)
    params["keyring_type"] = "rgw"
    return keyring_purge(**params)


def mon_is(**kwargs):
    """
    Is this a mon node

    Args:
        **kwargs: Arbitrary keyword arguments.
            mon_name : Set the mon_name.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    return mon.mon_is(**kwargs)


def mon_status(**kwargs):
    """
    Get status from mon deamon

    Args:
        **kwargs: Arbitrary keyword arguments.
            mon_name : Set the mon_name.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    return mon.mon_status(**kwargs)


def mon_quorum(**kwargs):
    """
    Is mon deamon in quorum

    Args:
        **kwargs: Arbitrary keyword arguments.
            mon_name : Set the mon_name.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    return mon.mon_quorum(**kwargs)



def mon_active(**kwargs):
    """
    Is mon deamon running

    Args:
        **kwargs: Arbitrary keyword arguments.
            mon_name : Set the mon_name.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    return mon.mon_active(**kwargs)


def mon_create(**kwargs):
    """
    Create a mon node

    Args:
        **kwargs: Arbitrary keyword arguments.
            mon_name : Set the mon serrvice name. Required
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    return mon.mon_create(**kwargs)


def mon_destroy(**kwargs):
    """
    Destroy a mon node

    Args:
        **kwargs: Arbitrary keyword arguments.
            mon_name : Set the mon serrvice name. Required
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    return mon.mon_destroy(**kwargs)


def mon_list(**kwargs):
    """
    Create a mon node

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    return mon.mon_list(**kwargs)


def rgw_pools_create(**kwargs):
    """
    Create pools for rgw
    """
    ctrl_rgw = rgw.rgw_ctrl(**kwargs)
    ctrl_rgw.update()
    return ctrl_rgw.rgw_pools_create()

def rgw_pools_missing(**kwargs):
    """
    Show pools missing for rgw
    """
    ctrl_rgw = rgw.rgw_ctrl(**kwargs)
    ctrl_rgw.update()
    return ctrl_rgw.rgw_pools_missing()


def rgw_create(**kwargs):
    """
    Create a rgw

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    ctrl_rgw = rgw.rgw_ctrl(**kwargs)
    ctrl_rgw.update()
    return ctrl_rgw.create()


def rgw_destroy(**kwargs):
    """
    Remove a rgw

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    ctrl_rgw = rgw.rgw_ctrl(**kwargs)
    ctrl_rgw.update()
    return ctrl_rgw.destroy()



def mds_create(**kwargs):
    """
    Create a mds

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    ctrl_mds = mds.mds_ctrl(**kwargs)
    ctrl_mds.update()
    return ctrl_mds.create()


def mds_destroy(**kwargs):
    """
    Remove a mds

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    ctrl_mds = mds.mds_ctrl(**kwargs)
    ctrl_mds.update()
    return ctrl_mds.destroy()


def keyring_auth_list(**kwargs):
    """
    List all cephx authorization keys

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    m = model.model(**kwargs)
    u = mdl_updater.model_updater(m)
    u.defaults_hostname()
    try:
        u.defaults_refresh()
    except:
        return {}
    u.load_confg(m.cluster_name)
    u.mon_members_refresh()
    auth_ops = ops_auth.ops_auth(m)
    auth_ops.auth_list()
    p = presenter.mdl_presentor(m)
    return p.auth_list()


def pool_list(**kwargs):
    """
    List all cephx authorization keys

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    m = model.model(**kwargs)
    u = mdl_updater.model_updater(m)
    u.defaults_hostname()
    try:
        u.defaults_refresh()
    except:
        return {}
    u.load_confg(m.cluster_name)
    u.mon_members_refresh()
    pool_ops = ops_pool.ops_pool(m)
    pool_ops.pool_list()
    p = presenter.mdl_presentor(m)
    return p.pool_list()



def pool_add(pool_name, **kwargs):
    """
    List all cephx authorization keys

    Args:
        pool_name: Pool to delete.
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
            pg_num : Default to 8
            pgp_num : Default to pg_num
            pool_type : can take values "replicated" or "erasure"
            erasure_code_profile : Set the "erasure_code_profile"
            crush_ruleset : Set the crush map rule set
    """
    m = model.model(**kwargs)
    u = mdl_updater.model_updater(m)
    u.defaults_hostname()
    u.defaults_refresh()
    u.load_confg(m.cluster_name)
    u.mon_members_refresh()
    pool_ops = ops_pool.ops_pool(m)
    pool_ops.pool_list()
    return pool_ops.pool_add(pool_name, **kwargs)


def pool_del(pool_name, **kwargs):
    """
    List all cephx authorization keys

    Args:
        pool_name: Pool to delete.
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    m = model.model(**kwargs)
    u = mdl_updater.model_updater(m)
    u.defaults_hostname()
    u.defaults_refresh()
    u.load_confg(m.cluster_name)
    u.mon_members_refresh()
    pool_ops = ops_pool.ops_pool(m)
    pool_ops.pool_list()
    return pool_ops.pool_del(pool_name)


def purge(**kwargs):
    """
    purge ceph configuration on the node

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
            hostname : Set the hostname. Defaults to the configured hostname.
    """
    m = model.model(**kwargs)
    purger.purge(m, **kwargs)


def ceph_version():
    """
    Get the version of ceph installed
    """
    m = model.model()
    u = mdl_updater.model_updater(m)
    u.ceph_version_refresh()
    p = presenter.mdl_presentor(m)
    return p.ceph_version()


def cluster_quorum(**kwargs):
    """
    Get the cluster status

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    m = model.model(**kwargs)
    u = mdl_updater.model_updater(m)
    u.defaults_hostname()
    u.defaults_refresh()
    u.load_confg(m.cluster_name)
    u.mon_members_refresh()
    cluster_ops = ops_cluster.ops_cluster(m)
    cluster_ops.status_refresh()
    q = mdl_query.mdl_query(m)
    return q.cluster_quorum()


def cluster_status(**kwargs):
    """
    Get the cluster status

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    m = model.model(**kwargs)
    u = mdl_updater.model_updater(m)
    u.defaults_hostname()
    u.defaults_refresh()
    u.load_confg(m.cluster_name)
    u.mon_members_refresh()
    cluster_ops = ops_cluster.ops_cluster(m)
    cluster_ops.status_refresh()
    p = presenter.mdl_presentor(m)
    return p.cluster_status()


def cephfs_ls(**kwargs):
    """
    List all cephfs file systems

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    m = model.model(**kwargs)
    u = mdl_updater.model_updater(m)
    u.defaults_hostname()
    u.defaults_refresh()
    u.load_confg(m.cluster_name)
    u.mon_members_refresh()
    cephfs_ops = ops_cephfs.ops_cephfs(m)
    cephfs_ops.cephfs_list()
    p = presenter.mdl_presentor(m)
    return p.cephfs_list()


def cephfs_add(fs_name, **kwargs):
    """
    Make new cephfs file system

    Args:
        fs_name: file system name to create
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
            pool_data : ceph pool to store data in.
            pool_metadata : ceph pool to store file system metadata in.
    """
    m = model.model(**kwargs)
    u = mdl_updater.model_updater(m)
    u.defaults_hostname()
    u.defaults_refresh()
    u.load_confg(m.cluster_name)
    u.mon_members_refresh()
    pool_ops = ops_pool.ops_pool(m)
    pool_ops.pool_list()
    # list the cephfs so we can check we need to do some thing
    cephfs_ops = ops_cephfs.ops_cephfs(m)
    cephfs_ops.cephfs_list()
    return cephfs_ops.cephfs_add(fs_name, **kwargs)


def cephfs_del(fs_name, **kwargs):
    """
    Make new cephfs file system

    Args:
        fs_name: file system name to destroy
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid : Set the cluster UUID. Defaults to value found in
                ceph config file.
            cluster_name : Set the cluster name. Defaults to "ceph".
    """
    m = model.model(**kwargs)
    u = mdl_updater.model_updater(m)
    u.defaults_hostname()
    u.defaults_refresh()
    u.load_confg(m.cluster_name)
    u.mon_members_refresh()
    cephfs_ops = ops_cephfs.ops_cephfs(m)
    # list the cephfs so we can check we need to do some thing
    cephfs_ops.cephfs_list()
    return cephfs_ops.cephfs_del(fs_name, **kwargs)
