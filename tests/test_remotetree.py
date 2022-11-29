'''test sftpretty.remotetree'''

from common import conn, VFS
from pathlib import Path
from sftpretty import Connection
from tempfile import mkdtemp


def test_remotetree(sftpserver):
    '''test the remotetree function, with recurse'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            cwd = sftp.pwd
            directories = {}
            localpath = Path(mkdtemp()).as_posix()

            sftp.remotetree(directories, cwd, localpath)

            dkeys = ['/home/test',
                     '/home/test/pub',
                     '/home/test/pub/foo2']

            dvalues = [[('/home/test/pub', f'{localpath}/home/test/pub')],
                       [('/home/test/pub/foo1',
                         f'{localpath}/home/test/pub/foo1'),
                        ('/home/test/pub/foo2',
                         f'{localpath}/home/test/pub/foo2')],
                       [('/home/test/pub/foo2/bar1',
                         f'{localpath}/home/test/pub/foo2/bar1')]]

            assert list(directories.keys()) == dkeys
            assert list(directories.values()) == dvalues


def test_remotetree_no_recurse(sftpserver):
    '''test the remotetree function, without recursing'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            cwd = sftp.pwd
            directories = {}
            localpath = Path(mkdtemp()).as_posix()

            sftp.remotetree(directories, cwd, localpath, recurse=False)

            dkeys = ['/home/test']
            dvalues = [[('/home/test/pub', f'{localpath}/home/test/pub')]]

            assert list(directories.keys()) == dkeys
            assert list(directories.values()) == dvalues
