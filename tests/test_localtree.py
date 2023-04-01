'''test sftpretty.localtree'''

from common import conn, rmdir, USER, USER_HOME_PARENT, VFS
from pathlib import Path
from sftpretty import Connection, localtree
from tempfile import mkdtemp


def test_localtree(sftpserver):
    '''test the localtree function, with recurse'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            localpath = mkdtemp()
            sftp.get_r('.', localpath)

            cwd = sftp.pwd
            tree = {}

            localtree(tree, localpath + cwd, Path(localpath).anchor)

            local = {
                f'{localpath}/{USER_HOME_PARENT}/{USER}': [
                    (f'{localpath}/{USER_HOME_PARENT}/{USER}/pub',
                     f'/{USER}/pub')
                ],
                f'{localpath}/{USER_HOME_PARENT}/{USER}/pub': [
                    (f'{localpath}/{USER_HOME_PARENT}/{USER}/pub/foo1',
                     f'/{USER}/pub/foo1'),
                    (f'{localpath}/{USER_HOME_PARENT}/{USER}/pub/foo2',
                     f'/{USER}/pub/foo2')
                ],
                f'{localpath}/{USER_HOME_PARENT}/{USER}/pub/foo2': [
                    (f'{localpath}/{USER_HOME_PARENT}/{USER}/pub/foo2/bar1',
                     f'/{USER}/pub/foo2/bar1')
                ]
            }

            for branch in sorted(tree.keys()):
                assert set(local[branch]) == set(tree[branch])
                del tree[branch]
            assert tree == {}

    rmdir(localpath)


def test_localtree_no_recurse(sftpserver):
    '''test the localtree function, without recursing'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            localpath = mkdtemp()
            sftp.chdir('pub/foo2')
            sftp.get_r('.', localpath)

            cwd = sftp.pwd
            tree = {}

            localtree(tree, localpath + cwd, Path(localpath).anchor,
                      recurse=False)

            local = {
                f'{localpath}/{USER_HOME_PARENT}/{USER}/pub/foo2': [
                    (f'{localpath}/{USER_HOME_PARENT}/{USER}/pub/foo2/bar1',
                     '/foo2/bar1')
                ]
            }

            for branch in sorted(tree.keys()):
                assert set(local[branch]) == set(tree[branch])
                del tree[branch]
            assert tree == {}

    rmdir(localpath)
