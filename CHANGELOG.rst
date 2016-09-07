0.2.0
-----
* Add new mon methods to allow life cycling mon roles.
  + mon_destroy
  + mon_list
* API change for mon_create require mon_name argument.

0.1.9
-----
* Add OSD reweight method.
    required for graceful decommissioning OSD.
* Add cephfs commands to allow adding removing and listing cephfs instances.
* Code refactoring to improve maintainability of cluster level operations.

0.1.8
-----
* Fix error messages for parsing ceph.conf.
* Avoid side effect of not being mon node.
* util.which fixes for running under salt.
* Add tox testing for python3.

0.1.7
-----
* Refactor rgw and mds to use common class to manage service keys.
* Add central constant for timeouts and use it where applicable.
  + Change default timeout to 20 seconds.
* Fix permissions on mds and rgw service keys.
* Enable mon daemons on boot.

0.1.6
-----
* Added new docstrings to many methods.
  + Old docstrings reflected the original salt useage best.
* Fixed issue dealing with ' ' in key names in ceph ${cluster}.conf files.

0.1.5
-----
* Fixed purge function not deleting keys.
* Fixed handling of floppy disks on target clusters
* Added new discover fields for disks and partitions.
  + disk
    - 'DRIVER',
    - 'SECTOR_SIZE_LOGICAL',
    - 'SECTOR_SIZE_PHYSICAL',
    - 'TABLE',
    - 'VENDOR_NAME'
  + partition
    - 'NUMBER',
    - 'SIZE_HUMAN'
* Added test for lsblk version.
* Added test for lsblk parsing
* Added test for parted parsing

0.1.4
-----
* Remove nose test from setup.py

0.1.3
-----
* Add flake8 and py.test infrastructure
* rgw: do not check for missing pools.
  + RGW pools have different names on Jewel.
  + these pools are auto created in Jewel.
  + Creating pools which are not used for the 2 reasons above only increases pg's/pgp's per osd.
  + Multi site/Multi zone does probably not need these standard rgw pools.

0.1.2
-----
* memoize the paths for executables only when they are found

0.1.1
-----
* Raise errors on missing executables.

0.1.0
-----
* Change code base to a library.
* Check for mds rgw commands

0.0.9
-----
* Bugfix Create bootstrapmon dir if missing.
* Documentation fixes

0.0.8
-----
* Rename module as ceph

0.0.7
------
* rgw keyring now more locked using profiles.
* mds keyring now more locked using profiles.
* improve logging of commands with spaces in attributes.

  * supporting cut and paste into bash.

0.0.6
------
* Update documentation to use new keyring functions.
* zap method to use kwargs.

0.0.5
------
* Allow "*auth_add" and "*auth_del" run not just on mon nodes.
* Add new public methods:

  * keyring_create
  * keyring_save
  * keyring_purge
  * keyring_present
  * keyring_auth_add
  * keyring_auth_del

0.0.4
------
* Add public methods cluster_quorum and cluster_status.
* Add to example file with cluster_status
* Add require into example file.
* Restructure cluster operations to make better time out handling.
