'''test sftpretty.localtree'''

from common import conn, rmdir, VFS
from pathlib import Path
from sftpretty import Connection, localtree
from tempfile import mkdtemp


def test_localtree(sftpserver):
    '''test the localtree function, with recurse'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            localpath = Path(mkdtemp()).as_posix()
            sftp.get_r('.', localpath)

            cwd = sftp.pwd
            tree = {}

            localtree(tree, localpath, cwd)

            local = {
                f'{localpath}': [
                    (f'{localpath}/pub', cwd + '/pub')
                ],
                f'{localpath}/pub': [
                    (f'{localpath}/pub/foo1', cwd + '/pub/foo1'),
                    (f'{localpath}/pub/foo2', cwd + '/pub/foo2')
                ],
                f'{localpath}/pub/foo2': [
                    (f'{localpath}/pub/foo2/bar1', cwd + '/pub/foo2/bar1')
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
            localpath = Path(mkdtemp()).as_posix()
            sftp.chdir('pub/foo2')
            sftp.get_r('.', localpath)

            cwd = sftp.pwd
            tree = {}

            localtree(tree, localpath, cwd, recurse=False)

            local = {
                f'{localpath}': [
                    (f'{localpath}/bar1', cwd + '/bar1')
                ]
            }

            for branch in sorted(tree.keys()):
                assert set(local[branch]) == set(tree[branch])
                del tree[branch]
            assert tree == {}

    rmdir(localpath)
