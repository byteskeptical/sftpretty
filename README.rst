sftpretty
=========

A pretty quick and simple interface to paramiko SFTP. Provides multi-threaded
routines with progress notifications through default callback, managed by an
optimized connection manager. This is a Python3 only fork of pysftp with
additional features and improvements.

* Built-in retry decorator
* Multi-threaded directory operations (get & put)
* Optimized remote & local tree functions
* Progress notifications
* Support for digests & kex connection options
* Support for ED25519 & ECDSA keys
* Support for private key passwords
* Thread-safe connection manager


Example
-------
.. code-block:: python

    from sftpretty import Connection

    # Basic

    with Connection('hostname', username='me', password='secret') as sftp:
        with sftp.cd('public'):             # temporarily chdir to public
            sftp.put('/my/local/filename')  # upload file to public/ on remote
            sftp.get('remote_file')         # get a remote file in the same dir

    with Connection('hostname', private_key='~/.ssh/id_ed25519',
                                private_key_pass='secret') as sftp:
        # upload local directory to remote_directory
        sftp.put_d('/my/local', '/remote_directory')

        # recursively get a remote_directory and save it to downloads locally
        sftp.get_r('remote_directory', '~/downloads')

    # Advanced

    with Connection('hostname', username='me', password='secret') as sftp:
        # upload local directory to remote_directory. On occurance of any
        # exception or child of passed in the tuple, retry the operation.
        # Between each attempt increment a pause equal to backoff * delay.
        # Run a total of tries (six) times including the first attempt.
        sftp.put_d('/my/local', '/remote_directory',
                   exceptions=(NoValidConnectionsError,
                               socket.timeout,
                               SSHException),
                   tries=6, backoff=2, delay=1)

    with Connection('hostname', private_key='~/.ssh/id_ed25519',
                                private_key_pass='secret') as sftp:
        # recursively get a remote_directory and save it to downloads locally
        # don't confirm files, useful in a scenario where the server removes
        # the remote file immediately after download. Preserve remote mtime in
        # local copy
        sftp.get_r('remote_directory', '~/downloads', confirm=False,
                   preserve_mtime=True)


Supports
--------
Tested on Python 3.5, 3.6, 3.7, 3.8, 3.9

.. image:: https://travis-ci.org/bornwitbugs/sftpretty.svg?branch=master
    :target: https://travis-ci.org/bornwitbugs/sftpretty

Additional Information
----------------------

* Project: https://github.com/bornwitbugs/sftpretty
* Download: https://pypi.python.org/pypi/sftpretty
* Documentation: Comming Soon!
* License: BSD

Requirements
------------
  paramiko >= 1.17.0
