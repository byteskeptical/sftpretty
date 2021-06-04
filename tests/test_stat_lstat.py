'''test sftpretty.stat and .lstat'''

from common import VFS, conn, SKIP_IF_CI
from sftpretty import Connection


def test_stat(sftpserver):
    '''test stat'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            dirname = 'pub'
            rslt = sftp.stat(dirname)
            assert rslt.st_size >= 0


@SKIP_IF_CI
def test_lstat(lsftp):
    '''test lstat  minimal, have to use real server, plugin doesn't support
    lstat'''
    dirname = 'pub'
    lsftp.mkdir(dirname)
    lsftp.chdir('/home/test')
    rslt = lsftp.lstat(dirname)
    lsftp.rmdir(dirname)
    assert rslt.st_size >= 0
