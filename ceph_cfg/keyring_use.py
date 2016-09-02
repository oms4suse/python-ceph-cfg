# Import Python Libs
from __future__ import absolute_import
import logging

# local modules
from . import model
from . import mdl_updater
from . import keyring
from . import utils
from . import ops_auth


log = logging.getLogger(__name__)


class Error(Exception):
    """
    Error
    """

    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [str(a) for a in self.args])


def _update_keyring_model(mdl):
    u = mdl_updater.model_updater(mdl)
    u.defaults_hostname()
    u.defaults_refresh()


def _update_auth_model(mdl):
    u = mdl_updater.model_updater(mdl)
    u.load_confg(mdl.cluster_name)
    u.mon_members_refresh()


def keyring_create_type(**kwargs):
    keyring_type = kwargs.get("keyring_type")
    if (keyring_type is None):
        raise Error("keyring_type is None")
    secret = kwargs.get("secret")
    m = model.model(**kwargs)
    mdl_updater.model_updater(m)
    _update_keyring_model(m)
    keyobj = keyring.keyring_facard(m)
    keyobj.key_type = keyring_type
    return keyobj.create(secret=secret)


def keyring_present_type(**kwargs):
    """
    Check if keyring exists on disk

    Args:
        **kwargs: Arbitrary keyword arguments.
            cluster_uuid
                Set the cluster UUID. Defaults to value found in ceph 
                config file.
            cluster_name
                Set the cluster name. Defaults to "ceph".
            keyring_type
                Set the keyring type
    """
    keyring_type = kwargs.get("keyring_type")
    if (keyring_type is None):
        raise Error("keyring_type is None")
    m = model.model(**kwargs)
    try:
        _update_keyring_model(m)
    except:
        pass
    keyobj = keyring.keyring_facard(m)
    keyobj.key_type = keyring_type
    return keyobj.present()


def keyring_purge_type(**kwargs):
    keyring_type = kwargs.get("keyring_type", None)
    if (keyring_type is None):
        raise Error("keyring_type is not set")
    m = model.model(**kwargs)
    _update_keyring_model(m)
    keyobj = keyring.keyring_facard(m)
    keyobj.key_type = keyring_type
    return keyobj.remove()


def keyring_save_type(**kwargs):
    keyring_type = kwargs.get("keyring_type")
    key_content = kwargs.get("key_content")
    secret = kwargs.get("secret")
    m = model.model(**kwargs)
    _update_keyring_model(m)
    keyobj = keyring.keyring_facard(m)
    keyobj.key_type = keyring_type
    if secret is not None:
        utils.is_valid_base64(secret)
        return keyobj.write_secret(secret)
    if key_content is not None:
        return keyobj.write_content(key_content)
    raise Error("Set either the key_content or the key `secret`")


def keyring_auth_add_type(**kwargs):
    keyring_type = kwargs.get("keyring_type")
    if (keyring_type is None):
        raise Error("keyring_type is None")
    if (keyring_type in set(["mon","admin"])):
        raise Error("keyring_type is %s" % (keyring_type))
    m = model.model(**kwargs)
    _update_keyring_model(m)
    _update_auth_model(m)
    keyobj = keyring.keyring_facard(m)
    keyobj.key_type = keyring_type
    if not keyobj.present():
        raise Error("keyring not present")
    auth_ops = ops_auth.ops_auth(m)
    return auth_ops.auth_add(keyring_type)


def keyring_auth_del_type(**kwargs):
    """
    Write rgw keyring for cluster

    Args:
        **kwargs: Arbitrary keyword arguments.
            keyring_type
                Set the keyring type
            cluster_uuid
                Set the cluster UUID. Defaults to value found in ceph config file.

            cluster_name
                Set the cluster name. Defaults to "ceph".
    """
    keyring_type = kwargs.get("keyring_type")
    if (keyring_type is None):
        raise Error("keyring_type is None")
    if (keyring_type in set(["mon","admin"])):
        raise Error("keyring_type is %s" % (keyring_type))
    m = model.model(**kwargs)
    _update_keyring_model(m)
    _update_auth_model(m)
    keyobj = keyring.keyring_facard(m)
    keyobj.key_type = keyring_type
    if not keyobj.present():
        raise Error("keyring not present")
    auth_ops = ops_auth.ops_auth(m)
    return auth_ops.auth_del(keyring_type)



