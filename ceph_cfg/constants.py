import os.path

JOURNAL_UUID = '45b0969e-9b03-4f30-b4c6-b4b80ceff106'
OSD_UUID = '4fbd7e29-9d25-41b8-afd0-062c0ceff05d'


_path_ceph_lib = "/var/lib/ceph/"
_path_ceph_lib_osd = os.path.join(_path_ceph_lib,"osd")
_path_ceph_lib_mon = os.path.join(_path_ceph_lib,"mon")
_path_ceph_lib_rgw = os.path.join(_path_ceph_lib,"radosgw")
_path_ceph_lib_mds = os.path.join(_path_ceph_lib,"mds")


# Make time out in seconds for remote operations
ceph_remote_call_timeout = 20
