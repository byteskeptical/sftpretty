'''test sftpretty.localtree'''

from common import conn, rmdir, USER, VFS
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

            localtree(tree, localpath, cwd)

            local = {
                f'{localpath}': [
                    (f'{localpath}/test', cwd)
                ],
                f'{localpath}/test': [
                    (f'{localpath}/test/pub', cwd + '/pub')
                ],
                f'{localpath}/test/pub': [
                    (f'{localpath}/test/pub/foo1', cwd + '/pub/foo1'),
                    (f'{localpath}/test/pub/foo2', cwd + '/pub/foo2')
                ],
                f'{localpath}/test/pub/foo2': [
                    (f'{localpath}/test/pub/foo2/bar1', cwd + '/pub/foo2/bar1')
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

            localtree(tree, localpath, cwd, recurse=False)

            local = {
                f'{localpath}/foo2': [
                    (f'{localpath}/foo2/bar1', cwd + '/bar1')
                ]
            }

            for branch in sorted(tree.keys()):
                assert set(local[branch]) == set(tree[branch])
                del tree[branch]
            assert tree == {}

    rmdir(localpath)
