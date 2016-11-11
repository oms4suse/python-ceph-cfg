import ceph_cfg.model
import ceph_cfg.keyring


class Test_keyring(object):
    def setup(self):
        mdl = ceph_cfg.model.model()
        mdl.cluster_name = "ceph"
        self.keyring = ceph_cfg.keyring.keyring_facard(mdl)


    def test_keyring_types_path_get(self):
        for keyring_type in ["admin", "mds", "mon", "osd", "rgw"]:
            self.keyring.key_type = keyring_type
            assert self.keyring.keyring_path_get() != None


    def test_keyring_types_keyring_identity(self):
        for keyring_type in ["admin", "mds", "mon", "osd", "rgw"]:
            self.keyring.key_type = keyring_type
            assert self.keyring.keyring_identity_get() != None
