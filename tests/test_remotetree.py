'''test sftpretty.remotetree'''

from common import conn, USER, VFS
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

            dkeys = [f'/home/{USER}',
                     f'/home/{USER}/pub',
                     f'/home/{USER}/pub/foo2']

            dvalues = [[(f'/home/{USER}/pub', f'{localpath}/home/{USER}/pub')],
                       [(f'/home/{USER}/pub/foo1',
                         f'{localpath}/home/{USER}/pub/foo1'),
                        (f'/home/{USER}/pub/foo2',
                         f'{localpath}/home/{USER}/pub/foo2')],
                       [(f'/home/{USER}/pub/foo2/bar1',
                         f'{localpath}/home/{USER}/pub/foo2/bar1')]]

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

            dkeys = [f'/home/{USER}']
            dvalues = [[(f'/home/{USER}/pub', f'{localpath}/home/{USER}/pub')]]

            assert list(directories.keys()) == dkeys
            assert list(directories.values()) == dvalues
