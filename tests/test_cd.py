'''test sftpretty.cd'''

import pytest

from common import conn, VFS, VFS_HOME
from pathlib import PurePosixPath
from sftpretty import Connection
from sftpretty.helpers import drivepath


def test_cd_none(sftpserver):
    '''test cd with None'''
    pubpath = PurePosixPath(drivepath(VFS_HOME)).joinpath('pub')
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            home = sftp.pwd
            with sftp.cd():
                sftp.chdir('pub')
                assert sftp.pwd == pubpath.as_posix()
            assert home == pubpath.parent.as_posix()


def test_cd_path(sftpserver):
    '''test cd with a path'''
    pubpath = PurePosixPath(drivepath(VFS_HOME)).joinpath('pub')
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            home = sftp.pwd
            with sftp.cd('pub'):
                assert sftp.pwd == pubpath.as_posix()
            assert home == pubpath.parent.as_posix()


def test_cd_nested(sftpserver):
    '''test nested cd's'''
    pubpath = PurePosixPath(drivepath(VFS_HOME)).joinpath('pub')
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            home = sftp.pwd
            with sftp.cd('pub'):
                assert sftp.pwd == pubpath.as_posix()
                with sftp.cd('foo1'):
                    assert sftp.pwd == pubpath.joinpath('foo1').as_posix()
                assert sftp.pwd == pubpath.as_posix()
            assert home == pubpath.parent.as_posix()


def test_cd_bad_path(sftpserver):
    '''test cd with a bad path'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            home = sftp.pwd
            with pytest.raises(IOError):
                with sftp.cd('not-there'):
                    pass
            assert home == drivepath(VFS_HOME)
