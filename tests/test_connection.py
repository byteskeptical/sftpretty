'''test sftpretty.Connection'''

import pytest
from paramiko import hostkeys

from common import conn, LOCAL, VFS
from pathlib import Path
from sftpretty import (CnOpts, Connection, ConnectionException,
                       SSHException)


@pytest.fixture
def ndp_sftpserver(sftpserver):
    '''non-default port sftpserver'''
    sftpserver.port = 8022
    return sftpserver


def test_connection_bad_credentials():
    '''attempt connection to a non-existing server'''
    copts = LOCAL.copy()
    copts['password'] = 'badword'
    del copts['private_key'], copts['private_key_pass']
    with pytest.raises(SSHException):
        with Connection(**copts) as sftp:
            sftp.listdir()


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


def test_connection_good(sftpserver):
    '''connect to a public sftp server'''
    with sftpserver.serve_content(VFS):
        sftp = Connection(**conn(sftpserver))
        sftp.close()


def test_connection_with(sftpserver):
    '''connect to a public sftp server'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            assert sftp.listdir() == ['pub', 'read.me']


def test_connection_non_default_port(ndp_sftpserver):
    '''connect to a public sftp server on non-default port'''
    with ndp_sftpserver.serve_content(VFS):
        non_conn = conn(ndp_sftpserver)
        non_conn['port'] = ndp_sftpserver.port
        with Connection(**non_conn) as sftp:
            assert sftp.listdir() == ['pub', 'read.me']


def test_connection_with_known_host_entry(sftpserver):
    '''connect to a public sftp server with known host entry'''
    hostkey = (f'[{sftpserver.host}]:{sftpserver.port} '
               'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB0g3SG/bbyysJ7f0kqdoWMXh'
               'HxxFR7aLJYNIHO/MtsD')
    knownhosts = Path('~/.ssh/known_hosts').expanduser()
    knownhosts.parent.mkdir(exist_ok=True, mode=0o700)
    knownhosts.touch(exist_ok=True, mode=0o644)
    knownhosts.write_bytes(bytes(hostkey))
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            assert sftp.listdir() == ['pub', 'read.me']


def test_connection_with_hashed_host(sftpserver):
    '''connect to a public sftp server with hashed host entry'''
    hashed_host = hostkeys.Hostkeys().hash_host(sftpserver.host)
    hostkey = (f'{hashed_host} '
               'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB0g3SG/bbyysJ7f0kqdoWMXh'
               'HxxFR7aLJYNIHO/MtsD')
    knownhosts = Path('~/.ssh/known_hosts').expanduser()
    knownhosts.parent.mkdir(exist_ok=True, mode=0o700)
    knownhosts.touch(exist_ok=True, mode=0o644)
    knownhosts.write_bytes(bytes(hostkey))
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            assert sftp.listdir() == ['pub', 'read.me']


def test_connection_with_hashed_host_non_default_port(ndp_sftpserver):
    '''connect to a public sftp server with hashed host entry on non-default port'''
    host_port = f'[{ndp_sftpserver.host}]:{ndp_sftpserver.port}'
    hashed_host_port = hostkeys.Hostkeys().hash_host(host_port)
    hostkey = (f'{hashed_host_port} '
               'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB0g3SG/bbyysJ7f0kqdoWMXh'
               'HxxFR7aLJYNIHO/MtsD')
    knownhosts = Path('~/.ssh/known_hosts').expanduser()
    knownhosts.parent.mkdir(exist_ok=True, mode=0o700)
    knownhosts.touch(exist_ok=True, mode=0o644)
    knownhosts.write_bytes(bytes(hostkey))
    with ndp_sftpserver.serve_content(VFS):
        non_conn = conn(ndp_sftpserver)
        non_conn['port'] = ndp_sftpserver.port
        with Connection(**non_conn) as sftp:
            assert sftp.listdir() == ['pub', 'read.me']
