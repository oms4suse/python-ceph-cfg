#Test units
import ceph_cfg.utils
import ceph_cfg.model
import ceph_cfg.mdl_updater
import ceph_cfg.presenter

import mock

out_lsblk = """NAME="/dev/vda" KNAME="/dev/vda" MAJ:MIN="254:0" FSTYPE="" MOUNTPOINT="" LABEL="" UUID="" PARTTYPE="" PARTLABEL="" PARTUUID="" PARTFLAGS="" RA="512" RO="0" RM="0" MODEL="" SERIAL="" SIZE="21474836480" STATE="" OWNER="root" GROUP="disk" MODE="brw-rw----" ALIGNMENT="0" MIN-IO="512" OPT-IO="0" PHY-SEC="512" LOG-SEC="512" ROTA="1" SCHED="" RQ-SIZE="128" TYPE="disk" DISC-ALN="0" DISC-GRAN="0" DISC-MAX="0" DISC-ZERO="0" WSAME="0" WWN="" RAND="0" PKNAME="" HCTL="" TRAN="" REV="" VENDOR="0x1af4"
NAME="/dev/vda1" KNAME="/dev/vda1" MAJ:MIN="254:1" FSTYPE="ext4" MOUNTPOINT="/boot" LABEL="" UUID="6820d2ff-0293-44c8-aaeb-af8b9a7ca719" PARTTYPE="0x83" PARTLABEL="" PARTUUID="000aab8b-01" PARTFLAGS="0x80" RA="512" RO="0" RM="0" MODEL="" SERIAL="" SIZE="1076887552" STATE="" OWNER="root" GROUP="disk" MODE="brw-rw----" ALIGNMENT="0" MIN-IO="512" OPT-IO="0" PHY-SEC="512" LOG-SEC="512" ROTA="1" SCHED="" RQ-SIZE="128" TYPE="part" DISC-ALN="0" DISC-GRAN="0" DISC-MAX="0" DISC-ZERO="0" WSAME="0" WWN="" RAND="0" PKNAME="/dev/vda" HCTL="" TRAN="" REV="" VENDOR=""
NAME="/dev/vda2" KNAME="/dev/vda2" MAJ:MIN="254:2" FSTYPE="swap" MOUNTPOINT="[SWAP]" LABEL="" UUID="04084022-67c0-4c8c-b0af-38896a4b6bf9" PARTTYPE="0x82" PARTLABEL="" PARTUUID="000aab8b-02" PARTFLAGS="" RA="512" RO="0" RM="0" MODEL="" SERIAL="" SIZE="1076887552" STATE="" OWNER="root" GROUP="disk" MODE="brw-rw----" ALIGNMENT="0" MIN-IO="512" OPT-IO="0" PHY-SEC="512" LOG-SEC="512" ROTA="1" SCHED="" RQ-SIZE="128" TYPE="part" DISC-ALN="0" DISC-GRAN="0" DISC-MAX="0" DISC-ZERO="0" WSAME="0" WWN="" RAND="0" PKNAME="/dev/vda" HCTL="" TRAN="" REV="" VENDOR=""
NAME="/dev/vda3" KNAME="/dev/vda3" MAJ:MIN="254:3" FSTYPE="xfs" MOUNTPOINT="/" LABEL="" UUID="087a7112-be91-4531-b228-92d2e61c736d" PARTTYPE="0x83" PARTLABEL="" PARTUUID="000aab8b-03" PARTFLAGS="" RA="512" RO="0" RM="0" MODEL="" SERIAL="" SIZE="19320012800" STATE="" OWNER="root" GROUP="disk" MODE="brw-rw----" ALIGNMENT="0" MIN-IO="512" OPT-IO="0" PHY-SEC="512" LOG-SEC="512" ROTA="1" SCHED="" RQ-SIZE="128" TYPE="part" DISC-ALN="0" DISC-GRAN="0" DISC-MAX="0" DISC-ZERO="0" WSAME="0" WWN="" RAND="0" PKNAME="/dev/vda" HCTL="" TRAN="" REV="" VENDOR=""
NAME="/dev/vdb" KNAME="/dev/vdb" MAJ:MIN="254:16" FSTYPE="" MOUNTPOINT="" LABEL="" UUID="" PARTTYPE="" PARTLABEL="" PARTUUID="" PARTFLAGS="" RA="512" RO="0" RM="0" MODEL="" SERIAL="" SIZE="21474836480" STATE="" OWNER="root" GROUP="disk" MODE="brw-rw----" ALIGNMENT="0" MIN-IO="512" OPT-IO="0" PHY-SEC="512" LOG-SEC="512" ROTA="1" SCHED="" RQ-SIZE="128" TYPE="disk" DISC-ALN="0" DISC-GRAN="0" DISC-MAX="0" DISC-ZERO="0" WSAME="0" WWN="" RAND="0" PKNAME="" HCTL="" TRAN="" REV="" VENDOR="0x1af4"
NAME="/dev/vdb1" KNAME="/dev/vdb1" MAJ:MIN="254:17" FSTYPE="xfs" MOUNTPOINT="/var/lib/ceph/osd/ceph-0" LABEL="" UUID="2e42d28a-60be-4bc2-ab63-9b94bc37614e" PARTTYPE="" PARTLABEL="" PARTUUID="" PARTFLAGS="" RA="512" RO="0" RM="0" MODEL="" SERIAL="" SIZE="16105061888" STATE="" OWNER="ceph" GROUP="ceph" MODE="brw-rw----" ALIGNMENT="0" MIN-IO="512" OPT-IO="0" PHY-SEC="512" LOG-SEC="512" ROTA="1" SCHED="" RQ-SIZE="128" TYPE="part" DISC-ALN="0" DISC-GRAN="0" DISC-MAX="0" DISC-ZERO="0" WSAME="0" WWN="" RAND="0" PKNAME="/dev/vdb" HCTL="" TRAN="" REV="" VENDOR=""
NAME="/dev/vdc" KNAME="/dev/vdc" MAJ:MIN="254:32" FSTYPE="" MOUNTPOINT="" LABEL="" UUID="" PARTTYPE="" PARTLABEL="" PARTUUID="" PARTFLAGS="" RA="512" RO="0" RM="0" MODEL="" SERIAL="" SIZE="21474836480" STATE="" OWNER="root" GROUP="disk" MODE="brw-rw----" ALIGNMENT="0" MIN-IO="512" OPT-IO="0" PHY-SEC="512" LOG-SEC="512" ROTA="1" SCHED="" RQ-SIZE="128" TYPE="disk" DISC-ALN="0" DISC-GRAN="0" DISC-MAX="0" DISC-ZERO="0" WSAME="0" WWN="" RAND="0" PKNAME="" HCTL="" TRAN="" REV="" VENDOR="0x1af4"
NAME="/dev/vdc1" KNAME="/dev/vdc1" MAJ:MIN="254:33" FSTYPE="xfs" MOUNTPOINT="/var/lib/ceph/osd/ceph-6" LABEL="" UUID="f5a949d2-e848-433d-856a-19d15bd280b1" PARTTYPE="" PARTLABEL="" PARTUUID="" PARTFLAGS="" RA="512" RO="0" RM="0" MODEL="" SERIAL="" SIZE="16105061888" STATE="" OWNER="ceph" GROUP="ceph" MODE="brw-rw----" ALIGNMENT="0" MIN-IO="512" OPT-IO="0" PHY-SEC="512" LOG-SEC="512" ROTA="1" SCHED="" RQ-SIZE="128" TYPE="part" DISC-ALN="0" DISC-GRAN="0" DISC-MAX="0" DISC-ZERO="0" WSAME="0" WWN="" RAND="0" PKNAME="/dev/vdc" HCTL="" TRAN="" REV="" VENDOR=""
NAME="/dev/vdd" KNAME="/dev/vdd" MAJ:MIN="254:48" FSTYPE="" MOUNTPOINT="" LABEL="" UUID="" PARTTYPE="" PARTLABEL="" PARTUUID="" PARTFLAGS="" RA="512" RO="0" RM="0" MODEL="" SERIAL="" SIZE="21474836480" STATE="" OWNER="root" GROUP="disk" MODE="brw-rw----" ALIGNMENT="0" MIN-IO="512" OPT-IO="0" PHY-SEC="512" LOG-SEC="512" ROTA="1" SCHED="" RQ-SIZE="128" TYPE="disk" DISC-ALN="0" DISC-GRAN="0" DISC-MAX="0" DISC-ZERO="0" WSAME="0" WWN="" RAND="0" PKNAME="" HCTL="" TRAN="" REV="" VENDOR="0x1af4"
NAME="/dev/vde" KNAME="/dev/vde" MAJ:MIN="254:64" FSTYPE="" MOUNTPOINT="" LABEL="" UUID="" PARTTYPE="" PARTLABEL="" PARTUUID="" PARTFLAGS="" RA="512" RO="0" RM="0" MODEL="" SERIAL="" SIZE="21474836480" STATE="" OWNER="root" GROUP="disk" MODE="brw-rw----" ALIGNMENT="0" MIN-IO="512" OPT-IO="0" PHY-SEC="512" LOG-SEC="512" ROTA="1" SCHED="" RQ-SIZE="128" TYPE="disk" DISC-ALN="0" DISC-GRAN="0" DISC-MAX="0" DISC-ZERO="0" WSAME="0" WWN="" RAND="0" PKNAME="" HCTL="" TRAN="" REV="" VENDOR="0x1af4"
NAME="/dev/vdf" KNAME="/dev/vdf" MAJ:MIN="254:80" FSTYPE="" MOUNTPOINT="" LABEL="" UUID="" PARTTYPE="" PARTLABEL="" PARTUUID="" PARTFLAGS="" RA="512" RO="0" RM="0" MODEL="" SERIAL="" SIZE="21474836480" STATE="" OWNER="root" GROUP="disk" MODE="brw-rw----" ALIGNMENT="0" MIN-IO="512" OPT-IO="0" PHY-SEC="512" LOG-SEC="512" ROTA="1" SCHED="" RQ-SIZE="128" TYPE="disk" DISC-ALN="0" DISC-GRAN="0" DISC-MAX="0" DISC-ZERO="0" WSAME="0" WWN="" RAND="0" PKNAME="" HCTL="" TRAN="" REV="" VENDOR="0x1af4"
"""

def mock_lsblk(command_attrib_list):
    output= {
        'stdout' : out_lsblk,
        'stderr' : "",
        'retcode' : 0
        }
    return output


class Test_mdl_updater_lsblk(object):
    def setup(self):
        """
        Make temp directory for tests and set as current working directory
        """
        self.model = ceph_cfg.model.model()
        self.updater = ceph_cfg.mdl_updater.model_updater(self.model)
        self.presenter = ceph_cfg.presenter.mdl_presentor(self.model)
        # We dont want to retest the versions of lsblk.
        self.model.lsblk_version.major = 2
        self.model.lsblk_version.minor = 25
        self.model.lsblk_version.revision = 0

    @mock.patch('ceph_cfg.utils.execute_local_command', mock_lsblk)
    def test_partitions_all_refresh_lsblk(self):
        self.updater.partitions_all_refresh_lsblk()
        assert len(self.model.lsblk.keys()) == 6
        vda_details = self.model.lsblk.get('/dev/vda')
        assert vda_details != None
        RAND = vda_details.get('RAND')
        assert RAND == '0'
        GROUP = vda_details.get('GROUP')
        assert GROUP == 'disk'        
        DISC_MAX = vda_details.get('DISC-MAX')
        assert DISC_MAX == '0'
        RQ_SIZE = vda_details.get('RQ-SIZE')
        assert RQ_SIZE == '128'
        MODE = vda_details.get('MODE')
        assert MODE == 'brw-rw----'
        ROTA = vda_details.get('ROTA')
        assert ROTA == '1'
        RM = vda_details.get('RM')
        assert RM == '0'
        RO = vda_details.get('RO')
        assert RO == '0'
        RA = vda_details.get('RA')
        assert RA == '512'
        partition = vda_details.get('PARTITION')
        assert len(partition.keys()) == 3
        partition_vda1 = partition.get('/dev/vda1')
        print partition_vda1
        partition_vda1 != None
        RAND = partition_vda1.get('RAND')
        assert RAND == '0'
        GROUP = partition_vda1.get('GROUP')
        assert GROUP == 'disk'
        OPT_IO = partition_vda1.get('OPT-IO')
        assert OPT_IO == '0'
        PARTTYPE = partition_vda1.get('PARTTYPE')
        assert PARTTYPE == '0x83'
        DISC_MAX = partition_vda1.get('DISC-MAX')
        assert DISC_MAX == '0'
        FSTYPE = partition_vda1.get('FSTYPE')
        assert FSTYPE == 'ext4'
        PARTFLAGS = partition_vda1.get('PARTFLAGS')
        assert PARTFLAGS == '0x80'
        RQ_SIZE = partition_vda1.get('RQ-SIZE')
        assert RQ_SIZE == '128'
        MODE = partition_vda1.get('MODE')
        assert MODE == 'brw-rw----'
        ROTA = partition_vda1.get('ROTA')
        assert ROTA == '1'
        RM = partition_vda1.get('RM')
        assert RM == '0'
        RO = partition_vda1.get('RO')
        assert RO == '0'
        RA = partition_vda1.get('RA')
        assert RA == '512'
        PARTUUID = partition_vda1.get('PARTUUID')
        assert PARTUUID == '000aab8b-01'
        DISC_ZERO = partition_vda1.get('DISC-ZERO')
        assert DISC_ZERO == '0'
        WSAME = partition_vda1.get('WSAME')
        assert WSAME == '0'
        NAME = partition_vda1.get('NAME')
        assert NAME == '/dev/vda1'
        MOUNTPOINT = partition_vda1.get('MOUNTPOINT')
        assert MOUNTPOINT == '/boot'
        SIZE = partition_vda1.get('SIZE')
        assert SIZE == '1076887552'
        MAJ_MIN = partition_vda1.get('MAJ:MIN')
        assert MAJ_MIN == '254:1'
        DISC_GRAN = partition_vda1.get('DISC-GRAN')
        assert DISC_GRAN == '0'
        UUID = partition_vda1.get('UUID')
        assert UUID == '6820d2ff-0293-44c8-aaeb-af8b9a7ca719'
        PKNAME = partition_vda1.get('PKNAME')
        assert PKNAME == '/dev/vda'
        DISC_ALN = partition_vda1.get('DISC-ALN')
        assert DISC_ALN == '0'
        ALIGNMENT = partition_vda1.get('ALIGNMENT')
        assert ALIGNMENT == '0'
        MIN_IO = partition_vda1.get('MIN-IO')
        assert MIN_IO == '512'
        OWNER = partition_vda1.get('OWNER')
        assert OWNER == 'root'
        KNAME = partition_vda1.get('KNAME')
        assert KNAME == '/dev/vda1'
        TYPE = partition_vda1.get('TYPE')
        assert TYPE == 'part'
        PHY_SEC = partition_vda1.get('PHY-SEC')
        assert PHY_SEC == '512'
        
