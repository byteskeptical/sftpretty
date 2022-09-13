Change Log
=========

1.0.3 (current, released 2022-09-13)
------------------------------------
    * added disabled algorithms Connection option for transport


1.0.2 (released 2022-09-09)
---------------------------
    * bug fix for typo in put_d()
    * added sort to localtree() for test continuity


1.0.1 (released 2022-07-22)
---------------------------
    * added key types Connection option for transport
    * bug fixes for close()
    * default to private key authentication
    * enabled timeout setting for channel and transport
    * improved host key logging
    * localtree & remotetree functions windows compatible
    * started hosting on PyPi
    * updated tests and CI pipeline 

1.0.0 (released 2021-06-06)
---------------------------
    * added ECDSA and ED25519 key support for authentication
    * added digest and kex Connection options for transport
    * added tests for additional functionality
    * default callback function for progress notifications
    * hash function added to helpers for file verification option
    * improved local and remote directory mapping
    * improved logging capabilities
    * replaced_sftp_connect with context aware channel manager
    * retry decorator for automated recovery from failure
    * switched to using pathlib for all local filepath operations
    * updated documentation and README with advanced examples
