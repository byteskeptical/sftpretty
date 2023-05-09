'''test sftpretty.stat and .lstat'''

from blddirs import build_dir_struct
from common import conn, rmdir, VFS
from pathlib import Path
from sftpretty import Connection
from tempfile import mkdtemp


def test_stat(sftpserver):
    '''test stat'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            dirname = 'pub'
            rslt = sftp.stat(dirname)
            assert rslt.st_size >= 0


def test_lstat(lsftp):
    '''test lstat minimal, have to use real server, plugin doesn't support
    lstat'''
    localpath = Path(mkdtemp()).as_posix()
    build_dir_struct(localpath)
    dirname = Path(localpath).joinpath('pub').as_posix()
    rslt = lsftp.lstat(dirname)

    assert rslt.st_size >= 0

    rmdir(localpath)
