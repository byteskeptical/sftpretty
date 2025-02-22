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
