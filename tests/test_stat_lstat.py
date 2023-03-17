'''test sftpretty.stat and .lstat'''

from common import conn, VFS
from pathlib import Path
from sftpretty import Connection


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
    dirname = 'pub'
    lsftp.mkdir(dirname)
    lsftp.chdir(Path.home().as_posix())
    rslt = lsftp.lstat(dirname)
    lsftp.rmdir(dirname)
    assert rslt.st_size >= 0
