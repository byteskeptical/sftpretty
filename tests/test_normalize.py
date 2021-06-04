'''test sftpretty.normalize'''

from common import VFS, conn
from sftpretty import Connection


def test_normalize(sftpserver):
    '''test the normalize function'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            assert sftp.normalize('make.txt') == '/home/test/make.txt'
            assert sftp.normalize('.') == '/home/test'
            assert sftp.normalize('pub') == '/home/test/pub'
            sftp.chdir('pub')
            assert sftp.normalize('.') == '/home/test/pub'


# TODO
# def test_normalize_symlink(sftp):
#     '''test normalize against a symlink'''
#     sftp.chdir('/home/test')
#     rsym = 'readme.sym'
#     assert sftp.normalize(rsym) == '/home/test/readme.txt'


def test_pwd(sftpserver):
    '''test the pwd property'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo2')
            assert sftp.pwd == '/home/test/pub/foo2'
            sftp.chdir('bar1')
            assert sftp.pwd == '/home/test/pub/foo2/bar1'
            sftp.chdir('../../foo1')
            assert sftp.pwd == '/home/test/pub/foo1'
