'''session level fixtures'''

import pytest

from common import conn, LOCAL, VFS
from paramiko.hostkeys import HostKeys
from sftpretty import CnOpts, Connection


def setup_server_hostkey(sftpserver):
    '''setup CI server host key before test suite'''
    with sftpserver.serve_content(VFS):
        _conn = conn(sftpserver)
        _conn['cnopts'].hostkeys = None
        with Connection(**_conn) as sftp:
            rsk = sftp.remote_server_key
            hks = HostKeys()
            hks.add(hostname=sftpserver.host,
                    keytype=rsk.get_name(),
                    key=rsk)
            hks.save('sftpserver.pub')


@pytest.fixture(scope='session')
def lsftp(request):
    '''setup a session long connection to the local sftp server'''
    cnopts = CnOpts(knownhosts=None)
    LOCAL['cnopts'] = cnopts
    lsftp = Connection(**LOCAL)
    request.addfinalizer(lsftp.close)
    return lsftp


@pytest.fixture(autouse=True, scope='session')
def setup_sftpserver(sftpserver):
    setup_server_hostkey(sftpserver)
    yield
