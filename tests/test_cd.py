'''test sftpretty.cd'''

import pytest

from blddirs import build_dir_struct
from common import conn, rmdir, VFS
from pathlib import Path
from sftpretty import Connection


def test_cd_none(sftpserver):
    '''test sftpretty.cd with None'''
    build_dir_struct(Path.home().as_posix())
    pubpath = Path.home().joinpath('pub')
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            home = sftp.pwd
            with sftp.cd():
                sftp.chdir('pub')
                assert sftp.pwd == pubpath.as_posix()
            assert home == pubpath.parent.as_posix()
    rmdir(Path.home().as_posix())


def test_cd_path(sftpserver):
    '''test sftpretty.cd with a path'''
    build_dir_struct(Path.home().as_posix())
    pubpath = Path.home().joinpath('pub')
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            home = sftp.pwd
            with sftp.cd('pub'):
                assert sftp.pwd == pubpath.as_posix()
            assert home == pubpath.parent.as_posix()
    rmdir(Path.home().as_posix())


def test_cd_nested(sftpserver):
    '''test nested cd's'''
    build_dir_struct(Path.home().as_posix())
    pubpath = Path.home().joinpath('pub')
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            home = sftp.pwd
            with sftp.cd('pub'):
                assert sftp.pwd == pubpath.as_posix()
                with sftp.cd('foo1'):
                    assert sftp.pwd == pubpath.joinpath('foo1').as_posix()
                assert sftp.pwd == pubpath.as_posix()
            assert home == pubpath.parent.as_posix()
    rmdir(Path.home().as_posix())


def test_cd_bad_path(sftpserver):
    '''test sftpretty.cd with a bad path'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            home = sftp.pwd
            with pytest.raises(IOError):
                with sftp.cd('not-there'):
                    pass
            assert home == Path.home().as_posix()
