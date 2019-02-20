'''common setup code for tests'''

import pytest

from contextlib import contextmanager
from os import close, getenv
from pathlib import Path
from sftpretty import CnOpts
from tempfile import mkstemp

# pytest-sftpserver plugin information
SFTP_INTERNAL = {'host': 'localhost', 'username': 'user', 'password': 'pw'}
# used if ptest-sftpserver plugin does not support what we are testing
SFTP_LOCAL = {'host': 'localhost', 'username': 'test', 'password': 'test1357'}

# can only reach public, read-only server from CI platform, only test locally
# if environment variable CI is set  to something to disable local tests
# the CI env var is set to true by both drone-io and travis
SKIP_IF_CI = pytest.mark.skipif(getenv('CI', '') > '', reason='Not Local')
# try:
#     stars8192 = bytes('*'*8192)
# except TypeError:
STARS8192 = '*'*8192


def conn(sftpsrv):
    '''return a dictionary holding argument info for the sftpretty client'''
    cnopts = CnOpts()
    cnopts.hostkeys.load('sftpserver.pub')
    return {'host': sftpsrv.host, 'port': sftpsrv.port, 'username': 'user',
            'password': 'pw', 'default_path': '/home/test', 'cnopts': cnopts}


def rmdir(dir):
    dir = Path(dir)
    for item in dir.iterdir():
        if item.is_dir():
            rmdir(item)
        else:
            item.unlink()
    dir.rmdir()


@contextmanager
def tempfile_containing(contents='', suffix=''):
    '''create a temporary file, with optional suffix and return the filename,
    cleanup when finished'''

    fd, temp_path = mkstemp(suffix=suffix)
    close(fd)     # close file descriptor handle returned by mkstemp

    with open(temp_path, 'wb') as fh:
        fh.write(contents.encode('utf-8'))

    try:
        yield temp_path
    finally:
        Path(temp_path).unlink()


# filesystem served by pytest-sftpserver plugin
VFS = {
    'home': {
        'test': {
            'pub': {
                'foo1': {
                    'foo1.txt': 'content of foo1.txt',
                    'image01.jpg': 'data for image01.jpg'
                },
                'make.txt': 'content of make.txt',
                'foo2': {
                    'bar1': {
                        'bar1.txt': 'contents bar1.txt'
                    },
                    'foo2.txt': 'content of foo2.txt'
                }
            },
            'read.me': 'contents of read.me'
        }
    }
}
