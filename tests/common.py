'''common setup code for tests'''

import pytest

from contextlib import contextmanager
from os import close, environ
from pathlib import Path
from sftpretty import CnOpts
from tempfile import mkstemp


PASS = 'tEst@!357'
SKIP_IF_CI = pytest.mark.skipif(environ.get('CI', '') > '', reason='Not Local')
SKIP_IF_MAC = pytest.mark.skipif(environ.get('RUNNER_OS', '') == 'macOS',
                                 reason='WhackMac')
SKIP_IF_WIN = pytest.mark.skipif(environ.get('RUNNER_OS', '') == 'Windows',
                                 reason='NoWinZone')
STARS8192 = '*' * 8192
USER = environ.get('USER', environ.get('USERNAME'))
USER_HOME = Path.home().as_posix()
USER_HOME_PARENT = Path(USER_HOME).parent.as_posix()


LOCAL = {'default_path': USER_HOME, 'host': 'localhost',
         'private_key': 'id_sftpretty', 'private_key_pass': PASS,
         'username': USER}


def conn(sftpsrv):
    '''return a dictionary holding argument info for the sftpretty client'''
    cnopts = CnOpts(knownhosts='sftpserver.pub')
    return {'cnopts': cnopts, 'default_path': '/home/test',
            'host': sftpsrv.host, 'port': sftpsrv.port,
            'private_key': 'id_sftpretty', 'private_key_pass': PASS,
            'username': USER}


def rmdir(dir):
    dir = Path(dir)
    for item in dir.iterdir():
        if item.is_dir():
            rmdir(item)
        else:
            item.unlink()
    dir.rmdir()


@contextmanager
def tempfile_containing(contents=STARS8192, suffix=''):
    '''create a temporary file, with optional suffix and return the filename,
    cleanup when finished'''

    fd, temp_path = mkstemp(suffix=suffix)
    close(fd)

    with open(temp_path, 'wb') as fh:
        fh.write(contents.encode('utf-8'))

    try:
        yield Path(temp_path).as_posix()
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
