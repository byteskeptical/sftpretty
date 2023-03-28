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

            directories = sftp.remotetree(cwd, cwd, localpath)

            dvalues = [
                (f'{cwd}/pub', f'{localpath}/pub'),
                (f'{cwd}/pub/foo1', f'{localpath}/pub/foo1'),
                (f'{cwd}/pub/foo2', f'{localpath}/pub/foo2'),
                (f'{cwd}/pub/foo2/bar1', f'{localpath}/pub/foo2/bar1'),
            ]
            sorted(directories)

            assert len(directories) == len(dvalues)
            assert sorted(directories) == sorted(dvalues)


def test_remotetree_no_recurse(sftpserver):
    '''test the remotetree function, without recursing'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            cwd = sftp.pwd
            localpath = Path(mkdtemp()).as_posix()

            directories = sftp.remotetree(cwd, cwd, localpath, recurse=False)
            dvalues = [(f'{cwd}/pub', f'{localpath}/pub')]

            assert len(directories) == len(dvalues)
            assert sorted(directories) == sorted(dvalues)
