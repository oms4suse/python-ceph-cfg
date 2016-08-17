import pytest
import ceph_cfg.utils


class Test_is_valid_base64(object):
    """
    Test base64 functionality
    """
    def test_should_fail(self):
        with pytest.raises(Exception) as ceph_cfg.utils.Error:
            ceph_cfg.utils.is_valid_base64(b"sdadasd")

    def test_sucess(self):
        ceph_cfg.utils.is_valid_base64(b'AQBR8KhWgKw6FhAAoXvTT6MdBE+bV+zPKzIo6w==')
