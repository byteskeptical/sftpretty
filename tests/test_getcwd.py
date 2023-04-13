'''test sftpretty.getcwd'''

from common import conn, VFS
from pathlib import Path
from sftpretty import Connection


def test_getcwd_none(sftpserver):
    '''test .getcwd with no default_path arg'''
    with sftpserver.serve_content(VFS):
        cnn = conn(sftpserver)
        cnn['default_path'] = None
        with Connection(**cnn) as sftp:
            assert sftp.getcwd() is None


def test_getcwd_default_path(sftpserver):
    '''test .getcwd when using default_path arg'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            assert sftp.getcwd() == '/home/test'


def test_getcwd_after_chdir(sftpserver):
    '''test getcwd after a chdir operation'''
    pubpath = Path('/home/test').joinpath('pub/foo1')
    with sftpserver.serve_content(VFS):
        cnn = conn(sftpserver)
        cnn['default_path'] = None
        with Connection(**cnn) as sftp:
            sftp.chdir(pubpath.as_posix())
            assert sftp.getcwd() == pubpath.as_posix()
