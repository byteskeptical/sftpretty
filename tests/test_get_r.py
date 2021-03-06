'''test sftpretty.get_r'''

from common import conn, rmdir, VFS
from pathlib import Path
from sftpretty import Connection
from tempfile import mkdtemp


def test_get_r(sftpserver):
    '''test the get_r for remotepath is pwd '.' '''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            localpath = mkdtemp()
            sftp.get_r('.', localpath)

            checks = [
                      ([''], ['home', 'read.me']),
                      (['home', 'pub'], ['foo1', 'foo2', 'make.txt']),
                      (['home', 'pub', 'foo1'], ['foo1.txt', 'image01.jpg']),
                      (['home', 'pub', 'foo2'], ['bar1', 'foo2.txt']),
                      (['home', 'pub', 'foo2', 'bar1'], ['bar1.txt', ]),
                     ]

            for pth, fls in checks:
                assert sorted([path.name
                               for path in Path(localpath).joinpath(
                                                *pth).iterdir()]) == fls

            # cleanup local
            rmdir(localpath)


def test_get_r_pwd(sftpserver):
    '''test the get_r for remotepath is pwd '/pub/foo2' '''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            localpath = mkdtemp()
            sftp.get_r('pub/foo2', localpath)

            checks = [
                      (['', ], ['home', 'pub']),
                      (['', 'pub', ], ['foo2', ]),
                      (['', 'pub', 'foo2'], ['bar1', 'foo2.txt']),
                      (['', 'pub', 'foo2', 'bar1'], ['bar1.txt', ]),
                     ]

            for pth, fls in checks:
                assert sorted([path.name
                               for path in Path(localpath).joinpath(
                                                *pth).iterdir()]) == fls

            # cleanup local
            rmdir(localpath)


def test_get_r_pathed(sftpserver):
    '''test the get_r for localpath, starting deeper then pwd '''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo2')
            localpath = mkdtemp()
            sftp.get_r('./bar1', localpath)

            checks = [
                      (['', ], ['bar1', ]),
                      (['', 'bar1'], ['bar1.txt', ]),
                     ]

            for pth, fls in checks:
                assert sorted([path.name
                               for path in Path(localpath).joinpath(
                                                *pth).iterdir()]) == fls

            # cleanup local
            rmdir(localpath)


def test_get_r_cdd(sftpserver):
    '''test the get_r for chdir('pub/foo2')'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            localpath = mkdtemp()
            sftp.chdir('pub/foo2')
            sftp.get_r('.', localpath)

            checks = [
                      (['', ], ['foo2.txt', 'home']),
                      (['bar1', ], ['bar1.txt', ]),
                     ]

            for pth, fls in checks:
                assert sorted([path.name
                               for path in Path(localpath).joinpath(
                                                *pth).iterdir()]) == fls

            # cleanup local
            rmdir(localpath)
