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
            directories = {}

            localtree(directories, localpath + cwd, Path(localpath).anchor)

            dkeys = [f'{localpath}/home/test',
                     f'{localpath}/home/test/pub',
                     f'{localpath}/home/test/pub/foo2']

            dvalues = [[(f'{localpath}/home/test/pub',
                         f'{localpath}/home/test/pub')],
                       [(f'{localpath}/home/test/pub/foo1',
                         f'{localpath}/home/test/pub/foo1'),
                        (f'{localpath}/home/test/pub/foo2',
                         f'{localpath}/home/test/pub/foo2')],
                       [(f'{localpath}/home/test/pub/foo2/bar1',
                         f'{localpath}/home/test/pub/foo2/bar1')]]

            assert sorted(directories.keys()) == dkeys
            assert sorted(directories.values()) == dvalues

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

            dkeys = [f'{localpath}/home/test/pub/foo2']

            dvalues = [[(f'{localpath}/home/test/pub/foo2/bar1',
                         f'{localpath}/home/test/pub/foo2/bar1')]]

            assert sorted(directories.keys()) == dkeys
            assert sorted(directories.values()) == dvalues

    # cleanup local
    rmdir(localpath)
