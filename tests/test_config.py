'''test CnOpts.config param'''

import pytest

from common import conn, LOCAL, PASS, USER, USER_HOME, VFS
from pathlib import Path
from sftpretty import (CnOpts, Connection, ConnectionException,
                       SSHException)


def test_connection_with_config(sftpserver):
    '''connect to a public sftp server'''
    config = Path(f'{USER_HOME}/.ssh/config')
    config.parent.mkdir(exist_ok=True, mode=0o700)
    config.touch(exist_ok=True, mode=0o644)
    config.write_bytes((b'host localhost'
                        bytes(f'  User {USER}'.encode('utf-8')))
    cnopts = CnOpts(config=config.as_posix(),
                    knownhosts='sftpserver.pub')
    with sftpserver.serve_content(VFS):
        with Connection('localhost', cnopts=cnopts, password=f'{PASS}') as sftp:
            assert sftp.listdir() == ['pub', 'read.me']


def test_connection_with_config_alias(sftpserver):
    '''connect to a public sftp server'''
    config = Path(f'{USER_HOME}/.ssh/config')
    config.parent.mkdir(exist_ok=True, mode=0o700)
    config.touch(exist_ok=True, mode=0o644)
    config.write_bytes((b'Host test'
                        b'    Hostname localhost'
                        bytes(f'    User {USER}'.encode('utf-8')))
    cnopts = CnOpts(config=config.as_posix(),
                    knownhosts='sftpserver.pub')
    with sftpserver.serve_content(VFS):
        with Connection('test', cnopts=cnopts, password=f'{PASS}') as sftp:
            assert sftp.listdir() == ['pub', 'read.me']


def test_connection_with_config_identity(sftpserver):
    '''connect to a public sftp server'''
    config = Path(f'{USER_HOME}/.ssh/config')
    config.parent.mkdir(exist_ok=True, mode=0o700)
    config.touch(exist_ok=True, mode=0o644)
    config.write_bytes((b'Host localhost'
                        b'    IdentityFile id_sftpretty'
                        bytes(f'    User {USER}'.encode('utf-8')))
    cnopts = CnOpts(config=config.as_posix(),
                    knownhosts='sftpserver.pub')
    with sftpserver.serve_content(VFS):
        with Connection('localhost', cnopts=cnopts,
                        private_key_pass=f'{PASS}') as sftp:
            assert sftp.listdir() == ['pub', 'read.me']
