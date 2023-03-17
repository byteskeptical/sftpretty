'''test sftpretty.isdir and sftpretty.isfile methods'''

from common import conn, VFS
from sftpretty import Connection


def test_isfile(sftpserver):
    '''test .isfile() functionality'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            rfile = 'pub/make.txt'
            rdir = 'pub'
            assert sftp.isfile(rfile)
            assert sftp.isfile(rdir) is False


# TODO
# def test_isfile_2(sftp):
#     '''test .isfile() functionality against a symlink'''
#     rsym = 'readme.sym'
#     assert sftp.isfile(rsym)


def test_isdir(sftpserver):
    '''test .isdir() functionality'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            rfile = 'pub/make.txt'
            rdir = 'pub'
            assert sftp.isdir(rfile) is False
            assert sftp.isdir(rdir)


# TODO
# def test_isdir_2(sftp):
#     '''test .isdir() functionality against a symlink'''
#     rsym = 'readme.sym'
#     assert sftp.isdir(rsym) is False
