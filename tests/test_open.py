'''test sftpretty.open'''

from common import VFS, conn
from sftpretty import Connection


def test_open_read(sftpserver):
    '''test the open function'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as psftp:
            psftp.chdir('pub')
            rfile = psftp.open('make.txt')
            contents = rfile.read()
            rfile.close()
            assert contents == b'content of make.txt'


def test_open_read_with(sftpserver):
    '''test the open function in a with statment'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as psftp:
            psftp.chdir('pub')
            with psftp.open('make.txt') as rfile:
                contents = rfile.read()
            assert contents == b'content of make.txt'
