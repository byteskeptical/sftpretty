'''test sftpretty.Connection'''

import pytest

from common import conn, SKIP_IF_CI, SFTP_LOCAL, VFS
from sftpretty import CnOpts, Connection, ConnectionException, SSHException


def test_connection_with(sftpserver):
    '''connect to a public sftp server'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            assert sftp.listdir() == ['pub', 'read.me']


def test_connection_bad_host():
    '''attempt connection to a non-existing server'''
    with pytest.raises(ConnectionException):
        cnopts = CnOpts()
        cnopts.hostkeys = None
        sftp = Connection(host='',
                          username='demo',
                          password='password',
                          cnopts=cnopts)
        sftp.close()


@SKIP_IF_CI
def test_connection_bad_credentials():
    '''attempt connection to a non-existing server'''
    copts = SFTP_LOCAL.copy()
    copts['password'] = 'badword'
    with pytest.raises(SSHException):
        with Connection(**copts) as sftp:
            sftp.listdir()


def test_connection_good(sftpserver):
    '''connect to a public sftp server'''
    with sftpserver.serve_content(VFS):
        sftp = Connection(**conn(sftpserver))
        sftp.close()
