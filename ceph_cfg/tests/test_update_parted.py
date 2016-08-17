#Test units
import ceph_cfg.utils
import ceph_cfg.model
import ceph_cfg.mdl_updater
import ceph_cfg.presenter
import ceph_cfg.util_which

import mock

parted_out = """BYT;
/dev/vda:21.5GB:virtblk:512:512:msdos:Virtio Block Device:;
1:1049kB:1078MB:1077MB:ext4::boot, type=83;
2:1078MB:2155MB:1077MB:linux-swap(v1)::type=82;
3:2155MB:21.5GB:19.3GB:xfs::type=83;

BYT;
/dev/vdb:21.5GB:virtblk:512:512:gpt:Virtio Block Device:;

BYT;
/dev/vdc:21.5GB:virtblk:512:512:gpt:Virtio Block Device:;

BYT;
/dev/vdd:21.5GB:virtblk:512:512:gpt:Virtio Block Device:;

BYT;
/dev/vde:21.5GB:virtblk:512:512:gpt:Virtio Block Device:;

BYT;
/dev/vdf:21.5GB:virtblk:512:512:gpt:Virtio Block Device:;

"""

def mock_util_which_parted():
    return '/usr/sbin/parted'

def mock_parted(command_attrib_list):
    output= {
        'stdout' : parted_out,
        'stderr' : "",
        'retcode' : 0
        }
    return output


class Test_mdl_updater_parted(object):
    def setup(self):
        """
        Make updater
        """
        self.model = ceph_cfg.model.model()
        self.updater = ceph_cfg.mdl_updater.model_updater(self.model)


    @mock.patch('ceph_cfg.util_which.memoise_which.path', mock_util_which_parted)
    @mock.patch('ceph_cfg.utils.execute_local_command', mock_parted)
    def test_partitions_all_refresh_parted(self):
        self.updater.partitions_all_refresh_parted()
        assert len(self.model.parted.keys()) == 6
        vda_details = self.model.parted.get('/dev/vda')
        assert vda_details != None
        vendor = vda_details.get('vendor')
        assert vendor == 'Virtio Block Device'
        table = vda_details.get('table')
        assert table == 'msdos'        
        disk = vda_details.get('disk')
        assert disk == '/dev/vda'
        sector_size_physical = vda_details.get('sector_size_physical')
        assert sector_size_physical == '512'
        sector_size_logical = vda_details.get('sector_size_logical')
        assert sector_size_logical == '512'
        driver = vda_details.get('driver')
        assert driver == 'virtblk'
        size = vda_details.get('size')
        assert size == '21.5GB'
        partition = vda_details.get('partition')
        assert len(partition.keys()) == 3
        partition_vda1 = partition.get('/dev/vda1')
        partition_vda1 != None
        Number = partition_vda1.get('Number')
        assert Number == '1'
        End = partition_vda1.get('End')
        assert End == '1078MB'
        Start = partition_vda1.get('Start')
        assert Start == '1049kB'
        fs = partition_vda1.get('File system')
        assert fs == 'ext4'
        Flags = partition_vda1.get('Flags')
        assert Flags == ['ext4']
        Path = partition_vda1.get('Path')
        assert Path == '/dev/vda1'
        Size = partition_vda1.get('Size')
        assert Size == '1077MB'
