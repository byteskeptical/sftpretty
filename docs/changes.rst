Change Log
=========
* 0.0.2 (current, released 2019-02-25)
    * default callback function to use for transfers
    * removed _sftp_connect and switched to context aware, thread-safe
      channels for all operations
    * added travis tests status for master branch to README
    * switched to using pathlib for all path operations
    * hash function added to helpers for file verification option (TODO)
    * retry decorator to preset recovery from failure in get and put
      operations
    * added ECDSA and ED25519 key formats for authentication
    * added kex and digest Connection options for transport
