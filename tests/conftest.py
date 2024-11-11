'''session level fixtures'''

import pytest
from paramiko.hostkeys import HostKeys
from pathlib import Path

from common import LOCAL
from sftpretty import CnOpts, Connection


@pytest.fixture(scope='session')
def lsftp(request):
    '''setup a session long connection to the local sftp server'''
    cnopts = CnOpts(knownhosts=None)
    LOCAL['cnopts'] = cnopts
    lsftp = Connection(**LOCAL)
    request.addfinalizer(lsftp.close)
    return lsftp


@pytest.fixture(autouse=True, scope='session')
def knownhosts(sftpserver):
    '''setup host key for test server in local knownhosts'''
    if sftpserver.port != 22:
        host = f'[{sftpserver.host}]:{sftpserver.port}'
    else:
        host = sftpserver.host
    hashed_host = HostKeys().hash_host(host)
    hashed_hostkey = (f'{hashed_host} '
                      'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB0g3SG/bbyysJ7f0kq'
                      'doWMXhHxxFR7aLJYNIHO/MtsD')
    hostkey = (f'{host} '
               'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB0g3SG/bbyysJ7f0kqdoWMXhH'
               'xxFR7aLJYNIHO/MtsD')
    knownhosts = Path('~/.ssh/known_hosts').expanduser()
    knownhosts.parent.mkdir(exist_ok=True, mode=0o700)
    knownhosts.touch(exist_ok=True, mode=0o644)
    knownhosts.write_bytes(bytes(hashed_hostkey, 'utf-8'))
    knownhosts.write_bytes(bytes(hostkey, 'utf-8'))

    yield
