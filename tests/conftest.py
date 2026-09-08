'''session level fixtures'''

import pytest

from common import LOCAL, remote_rmdir, STARS8192, USER_HOME
from os import close
from paramiko.hostkeys import HostKeys
from pathlib import Path
from sftpretty import CnOpts, Connection
from tempfile import mkstemp
from uuid import uuid4


@pytest.fixture(scope='session')
def lsftp(request):
    '''setup a session long connection to the local sftp server'''
    cnopts = CnOpts(knownhosts=None)
    LOCAL['cnopts'] = cnopts
    lsftp = Connection(**LOCAL)
    request.addfinalizer(lsftp.close)

    return lsftp


@pytest.fixture(autouse=True, scope='module')
def knownhosts(sftpserver, key_type='ssh-ed25519'):
    '''setup host key for test server in local knownhosts'''
    if sftpserver.port != 22:
        host = f'[{sftpserver.host}]:{sftpserver.port}'
    else:
        host = sftpserver.host
    host_hashed = HostKeys().hash_host(host)
    hostkey = \
        'AAAAC3NzaC1lZDI1NTE5AAAAIB0g3SG/bbyysJ7f0kqdoWMXhHxxFR7aLJYNIHO/MtsD'
    hostkeys = f'''\
        {host} {key_type} {hostkey}
        {host_hashed} {key_type} {hostkey}'''
    knownhosts = Path('sftpserver.pub')
    knownhosts.write_bytes(bytes(hostkeys, 'utf-8'))

    return


@pytest.fixture
def remote_tmpdir(lsftp):
    '''setup unique remote temporary directory'''
    remotedir = Path(USER_HOME).joinpath(f'sftpretty-{uuid4().hex[:8]}')
    lsftp.mkdir_p(remotedir.as_posix())

    try:
        yield lsftp.normalize(remotedir.as_posix())
    finally:
        remote_rmdir(lsftp, remotedir.as_posix())


@pytest.fixture
def tempfile_containing(tmp_path):
    '''create a temporary file, with optional suffix, holding content and
    return the filename'''
    def contentfile(contents=STARS8192, suffix=''):
        fd, temp_path = mkstemp(dir=tmp_path, suffix=suffix)
        close(fd)

        with open(temp_path, 'wb') as tempfile:
            tempfile.write(contents.encode('utf-8'))

        return Path(temp_path).as_posix()

    return contentfile
