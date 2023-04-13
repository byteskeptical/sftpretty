'''test sftpretty.normalize'''

from common import VFS, conn
from pathlib import Path
from sftpretty import Connection


def test_normalize(sftpserver):
    '''test the normalize function'''
    pubpath = Path('/home/test').joinpath('pub')
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            makepath = pubpath.parent.joinpath('make.txt').as_posix()
            assert sftp.normalize('make.txt') == makepath
            assert sftp.normalize('.') == pubpath.parent.as_posix()
            assert sftp.normalize('pub') == pubpath.as_posix()
            sftp.chdir('pub')
            assert sftp.normalize('.') == pubpath.as_posix()


# TODO
# def test_normalize_symlink(sftp):
#     '''test normalize against a symlink'''
#     home = Path.home()
#     sftp.chdir(home.as_posix())
#     rsym = 'readme.sym'
#     assert sftp.normalize(rsym) == home.joinpath(rsym).as_posix()


def test_pwd(sftpserver):
    '''test the pwd property'''
    pubpath = Path('/home/test').joinpath('pub')
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo2')
            assert sftp.pwd == pubpath.joinpath('foo2').as_posix()
            sftp.chdir('bar1')
            assert sftp.pwd == pubpath.joinpath('foo2/bar1').as_posix()
            sftp.chdir('../../foo1')
            assert sftp.pwd == pubpath.joinpath('foo1').as_posix()
