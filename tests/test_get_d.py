'''test sftpretty.get_d'''

from common import conn, rmdir, VFS
from pathlib import Path
from sftpretty import Connection
from tempfile import mkdtemp


def test_get_d(sftpserver):
    '''test the get_d for remotepath is pwd '.' '''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub')
            localpath = Path(mkdtemp()).as_posix()
            sftp.get_d('.', localpath)

            checks = [(['', ], ['make.txt', ]), ]
            for pth, fls in checks:
                assert sorted([
                    path.name
                    for path in Path(localpath).joinpath(*pth).iterdir()
                ]) == fls

            # cleanup local
            rmdir(localpath)


def test_get_d_pathed(sftpserver):
    '''test the get_d for localpath, starting deeper then pwd '''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub')
            localpath = Path(mkdtemp()).as_posix()
            sftp.get_d('foo1', localpath)

            checks = [(['', ], ['foo1.txt', 'image01.jpg']), ]
            for pth, fls in checks:
                assert sorted([
                    path.name
                    for path in Path(localpath).joinpath(*pth).iterdir()
                ]) == fls

            # cleanup local
            rmdir(localpath)
