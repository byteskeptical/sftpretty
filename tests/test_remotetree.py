'''test sftpretty.remotetree'''

from common import conn, VFS, VFS_HOME
from pathlib import Path
from sftpretty import Connection
from sftpretty.helpers import drivepath
from tempfile import mkdtemp


def test_remotetree(sftpserver):
    '''test the remotetree function, with recurse'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            cwd = sftp.pwd
            localpath = Path(mkdtemp()).as_posix()
            testpath = drivepath(VFS_HOME)
            tree = {}

            sftp.remotetree(tree, cwd, localpath)

            remote = {
                f'{testpath}': [
                    (f'{testpath}/pub', f'{localpath}/pub')
                ],
                f'{testpath}/pub': [
                    (f'{testpath}/pub/foo1',
                     f'{localpath}/pub/foo1'),
                    (f'{testpath}/pub/foo2',
                     f'{localpath}/pub/foo2')
                ],
                f'{testpath}/pub/foo2': [
                    (f'{testpath}/pub/foo2/bar1',
                     f'{localpath}/pub/foo2/bar1')
                ]
            }

            for branch in sorted(tree.keys()):
                assert set(remote[branch]) == set(tree[branch])
                del tree[branch]
            assert tree == {}


def test_remotetree_no_recurse(sftpserver):
    '''test the remotetree function, without recursing'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            cwd = sftp.pwd
            localpath = Path(mkdtemp()).as_posix()
            testpath = drivepath(VFS_HOME)
            tree = {}

            sftp.remotetree(tree, cwd, localpath, recurse=False)

            remote = {
                f'{testpath}': [
                    (f'{testpath}/pub', f'{localpath}/pub')
                ]
            }

            for branch in sorted(tree.keys()):
                assert set(remote[branch]) == set(tree[branch])
                del tree[branch]
            assert tree == {}
