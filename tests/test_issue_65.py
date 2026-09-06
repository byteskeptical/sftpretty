'''use the cd contextmanager prior to paramiko establishing a directory
location'''

from common import conn, VFS, VFS_HOME
from pathlib import PurePosixPath
from sftpretty import Connection
from sftpretty.helpers import drivepath


def test_issue_65(sftpserver):
    '''using the .cd() context manager prior to setting a directory
    via chdir causes an error'''
    pubpath = PurePosixPath(drivepath(VFS_HOME)).joinpath('pub')
    with sftpserver.serve_content(VFS):
        cnn = conn(sftpserver)
        cnn['default_path'] = None
        with Connection(**cnn) as sftp:
            assert sftp.getcwd() == pubpath.root
            with sftp.cd(pubpath.as_posix()):
                pass

            assert sftp.getcwd() == pubpath.root
