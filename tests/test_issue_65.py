'''use the cd contextmanager prior to paramiko establishing a directory
location'''

from common import conn, VFS
from pathlib import Path
from sftpretty import Connection


def test_issue_65(sftpserver):
    '''using the .cd() context manager prior to setting a directory
    via chdir causes an error'''
    pubpath = Path('/home/test').joinpath('pub')
    with sftpserver.serve_content(VFS):
        cnn = conn(sftpserver)
        cnn['default_path'] = None
        with Connection(**cnn) as sftp:
            assert sftp.getcwd() is None
            with sftp.cd(pubpath.as_posix()):
                pass

            assert sftp.getcwd() == '/'
