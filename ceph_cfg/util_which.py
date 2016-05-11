import logging

# analagous to the unix command which but with memoization functions.
try:
    from salt.utils import which as find_executable
except:
    from distutils.spawn import find_executable

log = logging.getLogger(__name__)


def Property(func):
    return property(**func())


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class ExecutableNotFound(Error):
    """
    Executable not found exception
    """
    def __init__(self, executable):
        self.executable = executable
        
    def __str__(self):
        return "Could not find executable '%s'" % (self.executable)


class memoise_which:
    """
    memoization of the which command
    """
    def __init__(self,exec_name):
        self.name = exec_name
        self._path = None


    @Property
    def path():
        doc = "the path to the exeutable"

        def fget(self):
            if not self._path is None:
                return self._path
            self._path = find_executable(self.name)
            if self._path is None:
                log.error("Could not find executable:", self.name)
                raise ExecutableNotFound(self.name)
            return self._path
        return locals()


which_ceph_authtool = memoise_which('ceph-authtool')
which_ceph_disk = memoise_which('ceph-disk')
which_ceph_mds = memoise_which('ceph-mds')
which_ceph = memoise_which('ceph')
which_ceph_mon = memoise_which('ceph-mon')
which_ceph_rgw = memoise_which('radosgw')
which_lsblk = memoise_which('lsblk')
which_partprobe = memoise_which('partprobe')
which_sgdisk = memoise_which('sgdisk')
which_systemctl = memoise_which('systemctl')
