'''test sftpretty.localtree'''

from common import conn, rmdir, USER, VFS
from pathlib import Path
from sftpretty import Connection, localtree
from tempfile import mkdtemp
from unittest.case import TestCase


def test_localtree(sftpserver):
    '''test the localtree function, with recurse'''
    test = TestCase
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            localpath = Path(mkdtemp()).as_posix()
            sftp.get_r('.', localpath)

            cwd = sftp.pwd
            tree = {}

            localtree(tree, localpath + cwd, Path(localpath).anchor)

            dkeys = [f'{localpath}/home/{USER}',
                     f'{localpath}/home/{USER}/pub',
                     f'{localpath}/home/{USER}/pub/foo2']

            dvalues = [[(f'{localpath}/home/{USER}/pub',
                         f'/{USER}/pub')],
                       [(f'{localpath}/home/{USER}/pub/foo1',
                         f'/{USER}/pub/foo1'),
                        (f'{localpath}/home/{USER}/pub/foo2',
                         f'/{USER}/pub/foo2')],
                       [(f'{localpath}/home/{USER}/pub/foo2/bar1',
                         f'/{USER}/pub/foo2/bar1')]]

            assert sorted(tree.keys()) == dkeys
            for branch in tree.values():
                for root in dvalues:
                    test.assertCountEqual(root, branch)

    # cleanup local
    rmdir(localpath)


def test_localtree_no_recurse(sftpserver):
    '''test the localtree function, without recursing'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            localpath = Path(mkdtemp()).as_posix()
            sftp.chdir('pub/foo2')
            sftp.get_r('.', localpath)

            cwd = sftp.pwd
            directories = {}

            localtree(directories, localpath + cwd, Path(localpath).anchor,
                      recurse=False)

            dkeys = [f'{localpath}/home/{USER}/pub/foo2']

            dvalues = [[(f'{localpath}/home/{USER}/pub/foo2/bar1',
                         '/foo2/bar1')]]

            assert sorted(directories.keys()) == dkeys
            assert sorted(directories.values()) == dvalues

    # cleanup local
    rmdir(localpath)
