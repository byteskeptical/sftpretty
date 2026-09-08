'''common setup code for tests'''

import pytest

from contextlib import contextmanager
from os import environ
from pathlib import Path
from sftpretty import CnOpts
from stat import S_ISDIR


PASS = 'tEst@!357'
SKIP_IF_CI = pytest.mark.skipif(environ.get('CI', '') > '', reason='Not Local')
SKIP_IF_MAC = pytest.mark.skipif(environ.get('RUNNER_OS', '') == 'macOS',
                                 reason='WhackMac')
SKIP_IF_ROOT = pytest.mark.skipif(environ.get('USER', '') == 'root',
                                  reason='RootRules')
SKIP_IF_WIN = pytest.mark.skipif(environ.get('RUNNER_OS', '') == 'Windows',
                                 reason='NoWinZone')
STARS8192 = '*' * 8192
USER = environ.get('USER', environ.get('USERNAME'))
USER_HOME = Path.home().as_posix()
USER_HOME_PARENT = Path(USER_HOME).parent.as_posix()
VFS = {
    'pub': {
        'foo1': {'foo1.txt': 'content of foo1.txt',
                 'image01.jpg': 'data for image01.jpg'},
        'make.txt': 'content of make.txt',
        'foo2': {'bar1': {'bar1.txt': 'contents bar1.txt'},
                 'foo2.txt': 'content of foo2.txt'}
    },
    'read.me': 'contents of read.me'
}
VFS_HOME = Path(USER_HOME_PARENT).joinpath('test').as_posix()


# filesystem served by pytest-sftpserver plugin
for node in reversed(VFS_HOME.strip('/').split('/')):
    VFS = {node: VFS}


LOCAL = {'default_path': USER_HOME, 'host': 'localhost',
         'private_key': 'id_sftpretty', 'private_key_pass': PASS,
         'username': USER}


def conn(sftpsrv):
    '''return a dictionary holding argument info for the sftpretty client'''
    cnopts = CnOpts(knownhosts='sftpserver.pub')
    cnopts.log_level = 'debug'
    return {'cnopts': cnopts, 'default_path': VFS_HOME,
            'host': sftpsrv.host, 'port': sftpsrv.port,
            'private_key': 'id_sftpretty', 'private_key_pass': PASS,
            'username': USER}


def remote_rmdir(sftp, dir):
    '''recursively remove a remote directory tree'''
    try:
        listing = sftp.listdir_attr(dir)
    except FileNotFoundError:
        return

    for attr in listing:
        remotepath = Path(dir).joinpath(attr.filename).as_posix()
        if S_ISDIR(attr.st_mode):
            remote_rmdir(sftp, remotepath)
        else:
            sftp.remove(remotepath)

    sftp.rmdir(dir)


def rmdir(dir):
    '''recursively remove a directory tree'''
    dir = Path(dir)
    for item in dir.iterdir():
        if item.is_dir():
            rmdir(item)
        else:
            item.unlink()
    dir.rmdir()
