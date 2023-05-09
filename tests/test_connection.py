'''test sftpretty.Connection'''

import pytest

from common import conn, LOCAL, VFS
from pathlib import Path
from sftpretty import (CnOpts, Connection, ConnectionException,
                       SSHException)


def test_connection_with(sftpserver):
    '''connect to a public sftp server'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            assert sftp.listdir() == ['pub', 'read.me']


def test_connection_bad_host():
    '''attempt connection to a non-existing server'''
    knownhosts = Path('~/.ssh/known_hosts').expanduser()
    knownhosts.parent.mkdir(exist_ok=True, mode=0o700)
    knownhosts.touch(exist_ok=True, mode=0o644)
    knownhosts.write_bytes((b'localhost ssh-ed25519 '
                            b'AAAAC3NzaC1lZDI1NTE5AAAAIB0g3SG/bbyysJ7f0kqdoWMX'
                            b'hHxxFR7aLJYNIHO/MtsD'))
    with pytest.raises(ConnectionException):
        cnopts = CnOpts()
        cnopts.hostkeys = None
        sftp = Connection('localhost.home.arpa', cnopts=CnOpts(),
                          password='badpass', username='badhost')
        sftp.listdir()


def test_connection_bad_credentials():
    '''attempt connection to a non-existing server'''
    copts = LOCAL.copy()
    copts['password'] = 'badword'
    del copts['private_key'], copts['private_key_pass']
    with pytest.raises(SSHException):
        with Connection(**copts) as sftp:
            sftp.listdir()


def test_connection_good(sftpserver):
    '''connect to a public sftp server'''
    with sftpserver.serve_content(VFS):
        sftp = Connection(**conn(sftpserver))
        sftp.close()
