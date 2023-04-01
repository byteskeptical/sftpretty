'''test sftpretty.remotetree'''

from common import conn, USER, USER_HOME_PARENT, VFS
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
                f'/{USER_HOME_PARENT}/{USER}': [
                    (f'/{USER_HOME_PARENT}/{USER}/pub', f'{localpath}/{USER}')
                ],
                f'/{USER_HOME_PARENT}/{USER}/pub': [
                    (f'/{USER_HOME_PARENT}/{USER}/pub/foo1',
                     f'{localpath}/{USER}/pub/foo1'),
                    (f'/{USER_HOME_PARENT}/{USER}/pub/foo2',
                     f'{localpath}/{USER}/pub/foo2')
                ],
                f'/{USER_HOME_PARENT}/{USER}/pub/foo2': [
                    (f'/{USER_HOME_PARENT}/{USER}/pub/foo2/bar1',
                     f'{localpath}/{USER}/pub/foo2/bar1')
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
                f'/{USER_HOME_PARENT}/{USER}': [
                    (f'/{USER_HOME_PARENT}/{USER}/pub', f'{localpath}/{USER}')
                ]
            }

            for branch in sorted(tree.keys()):
                assert set(remote[branch]) == set(tree[branch])
                del tree[branch]
            assert tree == {}
