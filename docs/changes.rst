Change Log
==========

1.0.6 (current, released 2023-01-15)
------------------------------------
    * allow CnOpts knownhost to be set to None directly
    * standardize on using is for None checks 

1.0.5 (released 2022-11-29)
------------------------------------
    * added log_level to connection options
    * added compression security option for Transport
    * code optimizations in _start_transport() and _set_authentication()
    * moved compression on/off switch to Connection object
    * sprinkled debug messaging throughout
    * switched to using native logging module instead of paramiko util

1.0.4 (released 2022-09-24)
------------------------------------
    * added Windows Pure Path logic in put_d() and put_r() through localtree()
    * fix for regression in _sftp_channel() causing UnboundLocalError
    * improved support for dot notation in known_hosts and private key file
    * removed basicConfig() call for improved embedded behavior

1.0.3 (released 2022-09-13)
---------------------------
    * added disabled algorithms option for Transport

1.0.2 (released 2022-09-09)
---------------------------
    * added sort to localtree() for test continuity
    * bug fix for typo in put_d()

1.0.1 (released 2022-07-22)
---------------------------
    * added key types security option for Transport
    * bug fixes for close()
    * default to private key authentication
    * enabled timeout setting for channel and transport
    * improved host key logging
    * localtree & remotetree functions Windows compatible
    * started hosting on PyPi
    * updated tests and CI pipeline 

1.0.0 (released 2021-06-06)
---------------------------
    * added ECDSA and ED25519 key support for authentication
    * added digest and kex security options for Transport
    * added tests for additional functionality
    * default callback function for progress notifications
    * hash function added to helpers for file verification option
    * improved local and remote directory mapping
    * improved logging capabilities
    * replaced _sftp_connect with context aware channel manager
    * retry decorator for automated recovery from failure
    * switched to using pathlib for all local filepath operations
    * updated documentation and README with advanced examples
