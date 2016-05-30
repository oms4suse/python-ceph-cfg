0.1.3
-----
* Add flake8 and py.test infrastructure
* rgw: do not check for missing pools.
  + RGW pools have different names on Jewel.
  + these pools are autocreated in Jewel.
  + Creating pools which are not used for the 2 reasons above only increases pg's/pgp's per osd.
  + Multisite/Multizone does probably not need these standard rgw pools.

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
