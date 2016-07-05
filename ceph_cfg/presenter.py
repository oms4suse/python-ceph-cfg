import logging

log = logging.getLogger(__name__)


class mdl_presentor():
    """
    Since presentation should be clean to the end user
    We abstract such functiosn in this class.
    """
    def __init__(self, model):
        self.model = model


    def _disks_all(self):
        disk_lsblk = set(self.model.lsblk.keys())
        disk_parted = set(self.model.parted.keys())
        return disk_lsblk.union(disk_parted)


    def _disk_partitions_lsblk(self, disk):
        partitions = set()
        disk_details = self.model.lsblk.get(disk)
        if disk_details is None:
            return partitions
        all_parts = disk_details.get('PARTITION')
        if all_parts is None:
            return partitions
        return set(all_parts.keys())


    def _disk_partitions_parted(self, disk):
        partitions = set()
        disk_details = self.model.lsblk.get(disk)
        if disk_details is None:
            return partitions
        all_parts = disk_details.get('PARTITION')
        if all_parts is None:
            return partitions
        return set(all_parts.keys())


    def _disk_partitions(self, disk):
        partitions_lsblk = self._disk_partitions_lsblk(disk)
        partitions_parted = self._disk_partitions_parted(disk)
        return partitions_lsblk.union(partitions_parted)


    def _partition_details_parted(self, disk, partition):
        output = {}
        details_disk = self.model.parted.get(disk)
        if details_disk == None:
            return output
        allpart = details_disk.get("partition")
        if allpart == None:
            log.debug("No partition info found:_partition_details_lsblk")
            return output
        details_partition = allpart.get(partition)
        if details_partition == None:
            log.debug("_partition_details_parted:No partition info found")
            log.debug(details_disk)
            return output
        data_mapper = {
                'Number' : 'NUMBER',
                'Size' : 'SIZE_HUMAN'
            }
        for key in data_mapper.keys():
            data = details_partition.get(key)
            if data == None:
                continue
            mapped_key = data_mapper.get(key)
            if mapped_key == None:
                continue
            output[mapped_key] = data
        return output


    def _partition_details_lsblk(self, disk, partition):
        output = {}
        details_disk = self.model.lsblk.get(disk)
        if details_disk == None:
            log.debug("No disk info found:_partition_details_lsblk")
            return output
        allpart = details_disk.get("PARTITION")
        if allpart == None:
            log.debug("No partition info found:_partition_details_lsblk")
            return output
        details_partition = allpart.get(partition)
        if details_partition == None:
            log.debug("No partition info found:_partition_details_lsblk")
            return output
        data_mapper = {
                'SIZE' : 'SIZE',
                'NAME' : 'NAME',
                'VENDOR' : 'VENDOR',
                'UUID' : 'UUID',
                'PARTLABEL' : 'PARTLABEL',
                'PKNAME' : 'PKNAME',
                'FSTYPE' : 'FSTYPE',
                'PARTTYPE' : 'PARTTYPE',
                'MOUNTPOINT' : 'MOUNTPOINT',
                'PARTUUID' : 'PARTUUID',
                'ROTA' : 'ROTA',
                'SCHED' : 'SCHED',
                'RQ-SIZE' : 'RQ-SIZE',
            }
        for key in data_mapper.keys():
            data = details_partition.get(key)
            if data == None:
                continue
            mapped_key = data_mapper.get(key)
            if mapped_key == None:
                continue
            output[mapped_key] = data
        return output


    def _partition_details(self, disk, partition):
        output = {}
        symlinks = self.model.symlinks.get(partition)
        if symlinks is not None:
            output["LINK"] = symlinks
        lsblk = self._partition_details_lsblk(disk, partition)
        output.update(lsblk)
        parted = self._partition_details_parted(disk, partition)
        output.update(parted)
        return output



    def _disk_details_parted(self, disk):
        output = {}
        details_disk = self.model.parted.get(disk)
        if details_disk == None:
            return output
        data_mapper = {
                'driver' : 'DRIVER',
                'sector_size_logical' : 'SECTOR_SIZE_LOGICAL',
                'sector_size_physical' : 'SECTOR_SIZE_PHYSICAL',
                'table' : 'TABLE',
                'vendor' : 'VENDOR_NAME'
            }
        for key in data_mapper.keys():
            data = details_disk.get(key)
            if data == None:
                continue
            mapped_key = data_mapper.get(key)
            if mapped_key == None:
                continue
            output[mapped_key] = data
        return output


    def _disk_details_lsblk(self, disk):
        output = {}
        details_disk = self.model.lsblk.get(disk)
        if details_disk == None:
            return output
        data_mapper = {
                'SIZE' : 'SIZE',
                'NAME' : 'NAME',
                'VENDOR' : 'VENDOR',
                'UUID' : 'UUID',
                'PARTLABEL' : 'PARTLABEL',
                'PKNAME' : 'PKNAME',
                'FSTYPE' : 'FSTYPE',
                'PARTTYPE' : 'PARTTYPE',
                'MOUNTPOINT' : 'MOUNTPOINT',
                'PARTUUID' : 'PARTUUID',
                'ROTA' : 'ROTA',
                'SCHED' : 'SCHED',
                'RQ-SIZE' :'RQ-SIZE'
            }
        for key in data_mapper.keys():
            data = details_disk.get(key)
            if data == None:
                continue
            mapped_key = data_mapper.get(key)
            if mapped_key == None:
                continue
            output[mapped_key] = data
        return output


    def _disk_details(self, disk):
        output = {}
        symlinks = self.model.symlinks.get(disk)
        if symlinks is not None:
            output["LINK"] = symlinks
        parted = self._disk_details_parted(disk)
        output.update(parted)
        lsblk = self._disk_details_lsblk(disk)
        output.update(lsblk)
        partitions = self._disk_partitions(disk)
        log.info("All partitons = %s" % (partitions))
        output["PARTITION"] = {}
        for part in partitions:
            partition_details = self._partition_details(disk, part)
            output["PARTITION"][part] = partition_details
        return output




    def lsblk_partition_by_disk_part(self, part):
        output = {}
        disk = self.model.part_pairent.get(part)
        if disk is None:
            return None
        disk_details = self.model.lsblk.get(disk)
        if disk_details is None:
            return None
        symlinks = self.model.symlinks.get(part)
        if symlinks is not None:
            output["LINK"] = symlinks
        wanted_keys = set([
                'SIZE',
                'NAME',
                'VENDOR',
                'UUID',
                'PARTLABEL',
                'PKNAME',
                'FSTYPE',
                'PARTTYPE',
                'MOUNTPOINT',
                'PARTUUID',
                'ROTA',
                'SCHED',
                'RQ-SIZE'
            ])

        all_parts = disk_details.get('PARTITION')
        if all_parts is None:
            return None
        part_details = all_parts.get(part)
        if part_details is None:
            return None
        for key in part_details:
            if not key in wanted_keys:
                continue
            output[key] = part_details.get(key)

        return output


    def partitions_all(self):
        '''
        List all partition details

        CLI Example::

            salt '*' sesceph.partitions_all
        '''
        output = {}
        for disk in self._disks_all():

            output[disk] = self._disk_details(disk)

        return output



    def discover_osd_by_cluster_uuid(self,cluster_uuid):
        osd_out_list = []
        osd_in_list = self.model.discovered_osd.get(cluster_uuid)
        if osd_in_list is None:
            return osd_out_list
        for osd_in in osd_in_list:
            osd_out = {}
            for key in osd_in.keys():
                if key in ["ceph_fsid", "dev_parent"]:
                    continue
                if key in [ "dev", "dev_journal"]:
                    osd_out[key] = self.lsblk_partition_by_disk_part(osd_in.get(key))
                    continue
                osd_out[key] = osd_in.get(key)
            osd_out_list.append(osd_out)
        return osd_out_list

    def discover_osd(self):
        output = {}
        for cluster in self.model.discovered_osd.keys():
            output[cluster] = self.discover_osd_by_cluster_uuid(cluster)
        return output

    def discover_osd_partitions(self):
        '''
        List all OSD and journal partitions

        CLI Example:

            salt '*' sesceph.discover_osd_partitions
        '''
        output = []
        for part_name in self.model.partitions_osd:
            part_info = self.lsblk_partition_by_disk_part(part_name)
            if part_info is None:
                continue
            output.append(part_info)
        return output

    def discover_journal_partitions(self):
        '''
        List all OSD and journal partitions

        CLI Example:

            salt '*' sesceph.discover_osd_partitions
        '''
        output = []
        for part_name in self.model.partitions_journal:
            part_info = self.lsblk_partition_by_disk_part(part_name)
            if part_info is None:
                continue
            output.append(part_info)
        return output

    def mon_status(self):
        """
        Present the monitor status
        """
        if (None == self.model.mon_status):
            return {}
        fsid = None
        output = {}
        for key in self.model.mon_status.keys():
            if key == 'monmap':
                monmap_in = self.model.mon_status.get(key)
                monmap_out = {}
                for monmap_key in monmap_in.keys():
                    if monmap_key == 'fsid':
                        fsid = monmap_in.get(monmap_key)
                        continue
                    monmap_out[monmap_key] = monmap_in.get(monmap_key)
                output[key] = monmap_out
                continue
            output[key] = self.model.mon_status.get(key)
        if fsid is None:
            return {}
        return {fsid : output}

    def cluster_status(self):
        """
        Present the cluster status
        """
        if (None == self.model.cluster_status):
            return {}
        fsid = None
        output = {}
        for key in self.model.cluster_status.keys():
            if key == 'monmap':
                monmap_in = self.model.cluster_status.get(key)
                monmap_out = {}
                for monmap_key in monmap_in.keys():
                    if monmap_key == 'fsid':
                        fsid = monmap_in.get(monmap_key)
                        continue
                    monmap_out[monmap_key] = monmap_in.get(monmap_key)
                output[key] = monmap_out
                continue
            output[key] = self.model.cluster_status.get(key)
        if fsid is None:
            return {}
        return {fsid : output}

    def auth_list(self):
        output = {}
        for keyname in self.model.auth_list.keys():
            section = {}
            keydetails = self.model.auth_list.get(keyname)
            for keysection in keydetails.keys():
                if keysection == "name":
                    continue
                section[keysection] = keydetails.get(keysection)
            output[keyname] = section
        return output


    def pool_list(self):
        return self.model.pool_list


    def ceph_version(self):
        output = {
            "major" : self.model.ceph_version.major,
            "minor" : self.model.ceph_version.minor,
            "revision" : self.model.ceph_version.revision,
            "uuid" : self.model.ceph_version.uuid
        }
        return output
