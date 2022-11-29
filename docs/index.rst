sftpretty
=========

A pretty quick and simple interface to paramiko SFTP. Provides multi-threaded
routines with progress notifications for reliable, asynchronous transfers. This
is a Python3 optimized fork of pysftp with additional features & improvements.

* Built-in retry decorator
* Hash function for integrity checking
* Improved local & remote directory mapping
* Improved logging mechanism
* More tests
* Multi-threaded directory transfers
* Progress notifications
* Support for ciphers, compression, digests, kex & key type connection options
* Support for disabled algorithms
* Support for ED25519 & ECDSA keys
* Support for private key passwords
* Thread-safe connection manager


Example
-------
.. code-block:: python

    from sftpretty import CnOpts, Connection


    # Basic

    with Connection('hostname', username='me', password='secret') as sftp:
        # Temporarily chdir to public/.
        with sftp.cd('public'):
            # Upload file to public/ on remote.
            sftp.put('/my/local/filename')
            # Download a remote file from public/.
            sftp.get('remote_file')


    with Connection('hostname', private_key='~/.ssh/id_ed25519',
                    private_key_pass='secret') as sftp:
        # Upload local directory to remote_directory.
        sftp.put_d('/my/local', '/remote_directory')

        # Recursively download a remote_directory and save it to /tmp locally.
        sftp.get_r('remote_directory', '/tmp')


    # Advanced

    # Use password authentication
    with Connection('hostname', username='me', password='secret') as sftp:
        # Upload local directory to remote_directory. On occurance of any
        # exception or child of, passed in the tuple, retry the operation.
        # Between each attempt increment a pause equal to backoff * delay.
        # Run a total of tries (six) times including the first attempt.
        sftp.put_d('/my/local', '/remote_directory', backoff=2, delay=1,
                   exceptions=(NoValidConnectionsError, socket.timeout,
                               SSHException), tries=6)

    # Use public key authentication with optional private key password
    with Connection('hostname', private_key='~/.ssh/id_ed25519',
                    private_key_pass='secret') as sftp:
        # Recursively download a remote_directory and save it to /tmp locally.
        # Don't confirm files, useful in a scenario where the server removes
        # the remote file immediately after download. Preserve remote mtime on
        # local copy
        sftp.get_r('remote_directory', '/tmp', confirm=False,
                   preserve_mtime=True)


    # Pass custom host key file for verification
    cnopts = CnOpts(knownhosts='sftpserver.pub')
    # Use connection options to set preferred encryption standards
    cnopts.ciphers= ('aes256-ctr', 'aes128-ctr')
    cnopts.digests = ('hmac-sha2-512', 'hmac-sha2-256')
    cnopts.kex = ('ecdh-sha2-nistp521', 'ecdh-sha2-nistp384')
    cnopts.key_types = ('ssh-ed25519', 'ecdsa-sha2-nistp521')
    # Turn on verbose logging and set custom log file
    cnopts.log = '/var/log/backups/daily.log'
    cnopts.log_level = 'debug'
    # Pass options object directly to connection object
    with Connection('hostname', cnopts=cnopts, private_key='~/.ssh/id_backup',
                    private_key_pass='secret') as sftp:
        # Aggressively retry important operation
        sftp.put_r('/local_backup', '/remote_backup', backoff=2, delay=1,
                   exceptions=socket.timeout, preserve_mtime=True, tries=11)


Additional Information
----------------------
* Project: https://github.com/byteskeptical/sftpretty
* Download: https://pypi.python.org/pypi/sftpretty
* Documentation: https://sftpretty.rtfd.org
* License: BSD

Requirements
------------
paramiko >= 1.17.0

Supports
--------
Tested on Python 3.6, 3.7, 3.8, 3.9, 3.10

Contents
--------

.. toctree::
   :maxdepth: 2

   cookbook
   sftpretty
   changes
   contributing
   authors

Indices & Tables
================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
