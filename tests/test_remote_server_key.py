'''test sftpretty.remote_server_key'''

import pytest

from common import conn, VFS
from paramiko.hostkeys import HostKeys
from paramiko.rsakey import RSAKey
from pathlib import Path
from sftpretty import CnOpts, Connection, HostKeysException, SSHException


def test_remote_server_key(sftpserver):
    '''test .remote_server_key property'''
    with sftpserver.serve_content(VFS):
        this_conn = conn(sftpserver)
        this_conn['cnopts'].hostkeys = None     # turn-off hostkey verification
        with Connection(**this_conn) as sftp:
            rsk = sftp.remote_server_key
            hks = HostKeys()
            hks.add(hostname=sftpserver.host,
                    keytype=rsk.get_name(),
                    key=rsk)
            hks.save('sftpserver.pub')


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


def test_hostkey_not_found():
    '''test that an exception is raised when no host key is found'''
    cnopts = CnOpts(knownhosts='sftpserver.pub')
    with pytest.raises(SSHException):
        cnopts.get_hostkey(host='missing-server')


def test_hostkey_returns_pkey():
    '''test the finding a matching host key returns a PKey'''
    cnopts = CnOpts(knownhosts='sftpserver.pub')
    assert isinstance(cnopts.get_hostkey('127.0.0.1'), RSAKey)
