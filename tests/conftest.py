'''session level fixtures'''

import pytest

from common import SFTP_LOCAL
from sftpretty import Connection


@pytest.fixture(scope="session")
def lsftp(request):
    '''setup a session long connection to the local sftp server'''
    lsftp = Connection(**SFTP_LOCAL)
    request.addfinalizer(lsftp.close)
    return lsftp  # provide the fixture value
