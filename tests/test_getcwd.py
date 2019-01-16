'''test sftpretty.getcwd
until you issue a .chdir/cwd command paramiko returns None for .getcwd,
unless you have set default_path in the Connection args'''

from common import conn, VFS
from sftpretty import Connection


def test_getcwd_none(sftpserver):
    '''test .getcwd as the first operation - need pristine connection
    and no default_path arg'''
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
    with sftpserver.serve_content(VFS):
        cnn = conn(sftpserver)
        cnn['default_path'] = None
        with Connection(**cnn) as sftp:
            sftp.chdir('/home/test/pub/foo1')
            assert sftp.getcwd() == '/home/test/pub/foo1'
