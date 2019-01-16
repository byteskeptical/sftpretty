sftpretty
======

A pretty quick and simple interface to SFTP. The module offers high level abstractions and
multi-threaded routines to handle your SFTP needs. Provides asynchronous file transfer with
progress notifications through default callback and a random hash function to boot.


Example
-------

::

    from sftpretty import Connection

    with Connection('hostname', username='me', password='secret') as sftp:
        with sftp.cd('public'):             # temporarily chdir to public
            sftp.put('/my/local/filename')  # upload file to public/ on remote
            sftp.get('remote_file')         # get a remote file

    with Connection('hostname', private_key='~/.ssh/id_rsa', private_key_pass='secret') as sftp:
        sftp.put_r('/my/local/filename', '/private')  # upload directory recursively 
                                                      # to private/ on remote
        sftp.get_d('remote_directory', '~/downloads') # get a remote directory


Supports
--------
[![Build Status](https://travis-ci.org/bornwitbugs/sftpretty.svg?branch=master)](https://travis-ci.org/bornwitbugs/sftpretty)

Tested on Python 3.3, 3.4, 3.5, 3.6, 3.7


Additional Information
----------------------

* Project: https://github.com/bornwitbugs/sftpretty
* Download: https://pypi.python.org/pypi/sftpretty
* Documentation: Comming Soon!
* License: BSD

Requirements
------------
paramiko >= 1.17.0
