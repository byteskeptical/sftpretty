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
            localpath = Path(mkdtemp()).as_posix()
            tree = {}

            sftp.remotetree(tree, cwd, localpath)

            remote = {
                '/home/test': [
                    ('/home/test/pub', f'{localpath}/pub')
                ],
                '/home/test/pub': [
                    ('/home/test/pub/foo1',
                     f'{localpath}/pub/foo1'),
                    ('/home/test/pub/foo2',
                     f'{localpath}/pub/foo2')
                ],
                '/home/test/pub/foo2': [
                    ('/home/test/pub/foo2/bar1',
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
            tree = {}

            sftp.remotetree(tree, cwd, localpath, recurse=False)

            remote = {
                '/home/test': [
                    ('/home/test/pub', f'{localpath}/pub')
                ]
            }

            for branch in sorted(tree.keys()):
                assert set(remote[branch]) == set(tree[branch])
                del tree[branch]
            assert tree == {}
