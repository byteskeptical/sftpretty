'''use the cd contextmanager prior to paramiko establishing a directory
location'''

from common import conn, VFS
from sftpretty import Connection
from sys import platform


def test_issue_65(sftpserver):
    '''using the .cd() context manager prior to setting a directory
    via chdir causes an error'''
    with sftpserver.serve_content(VFS):
        cnn = conn(sftpserver)
        cnn['default_path'] = None  # don't call .chdir by setting default_path
        with Connection(**cnn) as sftp:
            assert sftp.getcwd() is None
            with sftp.cd('/home/test/pub'):
                pass

            if platform.startswith('linux'):
                assert sftp.getcwd() == '/'
            elif platform.startswith('win32'):
                assert sftp.getcwd() is None
