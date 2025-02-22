'''test sftpretty.Connection'''

import pytest
from paramiko.hostkeys import HostKeys
from paramiko.ed25519key import Ed25519Key

from common import conn, LOCAL, VFS
from pathlib import Path
from sftpretty import (CnOpts, Connection, ConnectionException,
                       HostKeysException, SSHException)


def test_cnopts_bad_knownhosts():
    '''test setting knownhosts to a not understood file'''
    with pytest.raises(HostKeysException):
        with pytest.raises(UserWarning):
            knownhosts = Path('~/knownhosts').expanduser().as_posix()
            Path(knownhosts).touch(mode=0o600)
            CnOpts(knownhosts=knownhosts)
            Path(knownhosts).unlink()


def test_cnopts_no_knownhosts():
    '''test setting knownhosts to a non-existant file'''
    with pytest.raises(UserWarning):
        CnOpts(knownhosts='i-m-not-there')


def test_cnopts_none_knownhosts():
    '''test setting knownhosts to None for those with no default known_hosts'''
    knownhosts = Path('~/.ssh/known_hosts').expanduser().as_posix()
    if Path(knownhosts).exists():
        Path(knownhosts).unlink()
    cnopts = CnOpts(knownhosts=None)
    assert cnopts.hostkeys is None


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


def test_hostkey_not_found():
    '''test that an exception is raised when no host key is found'''
    cnopts = CnOpts(knownhosts='sftpserver.pub')
    with pytest.raises(SSHException):
        cnopts.get_hostkey(host='missing-server')


def test_hostkey_returns_pkey(sftpserver):
    '''test that finding a matching host key returns a PKey'''
    if sftpserver.port != 22:
        host = f'[{sftpserver.host}]:{sftpserver.port}'
    else:
        host = sftpserver.host

    cnopts = CnOpts(knownhosts='sftpserver.pub')
    assert isinstance(cnopts.get_hostkey(host), Ed25519Key)
