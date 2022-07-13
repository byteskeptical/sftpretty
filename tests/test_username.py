'''test username parameter'''

# pylint: disable=W0212

import pytest

from common import conn, VFS
from os import environ
from sftpretty import Connection, CredentialException


def test_username_specified(sftpserver):
    '''test specifying username as parameter'''
    with sftpserver.serve_content(VFS):
        params = conn(sftpserver)
        params['username'] = 'bob'
        with Connection(**params) as sftp:
            assert sftp._username == params['username']


def test_username_from_environ(sftpserver):
    '''test reading username from $LOGNAME environment variable.'''
    username = 'bob'
    hold_logname = environ.get('LOGNAME')
    environ['LOGNAME'] = username
    with sftpserver.serve_content(VFS):
        params = conn(sftpserver)
        del params['username']
        with Connection(**params) as sftp:
            if hold_logname is not None:
                environ['LOGNAME'] = hold_logname
            assert sftp._username == username


def test_no_username_raises_err(sftpserver):
    '''test No username raises CredentialException.'''
    hold_logname = environ.get('LOGNAME')
    del environ['LOGNAME']
    with sftpserver.serve_content(VFS):
        params = conn(sftpserver)
        del params['username']
        with pytest.raises(CredentialException):
            sftp = Connection(**params)
            sftp.close()
    if hold_logname is not None:
        environ['LOGNAME'] = hold_logname
