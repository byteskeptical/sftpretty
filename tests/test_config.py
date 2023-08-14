'''test CnOpts.config param'''

from common import conn, SKIP_IF_MAC, PASS, USER, USER_HOME, VFS
from pathlib import Path
from sftpretty import CnOpts, Connection


@SKIP_IF_MAC
# Mac-holes can't be trusted to update user passwords without the old one,
# even root
def test_connection_with_config(sftpserver):
    '''connect to a public sftp server using OpenSSH config'''
    config = Path(f'{USER_HOME}/.ssh/config')
    config.parent.mkdir(exist_ok=True, mode=0o700)
    config.touch(exist_ok=True, mode=0o644)
    with sftpserver.serve_content(VFS):
        config.write_bytes(bytes(('Host 127.0.0.1\n\t'
                                  f'Port {sftpserver.port}\n\t'
                                  f'User {USER}').encode('utf-8')))
        cnopts = CnOpts(config=config.as_posix(), knownhosts='sftpserver.pub')
        params = conn(sftpserver)
        params['cnopts'] = cnopts
        params['password'] = PASS
        del params['port']
        del params['private_key']
        del params['private_key_pass']
        del params['username']
        with Connection(**params) as sftp:
            assert sftp.listdir() == ['pub', 'read.me']
    config.unlink()


def test_connection_with_config_alias(sftpserver):
    '''connect to a public sftp server using OpenSSH config alias'''
    config = Path(f'{USER_HOME}/.ssh/config')
    config.parent.mkdir(exist_ok=True, mode=0o700)
    config.touch(exist_ok=True, mode=0o644)
    config.write_bytes(bytes(('Host test\n\t'
                              'Ciphers aes256-ctr,aes192-ctr\n\t'
                              'Hostname 127.0.0.1\n\t'
                              'IdentityFile id_sftpretty\n\t'
                              f'User {USER}').encode('utf-8')))
    cnopts = CnOpts(config=config.as_posix(), knownhosts='sftpserver.pub')
    with sftpserver.serve_content(VFS):
        params = conn(sftpserver)
        params['cnopts'] = cnopts
        params['host'] = 'test'
        del params['private_key']
        del params['username']
        with Connection(**params) as sftp:
            local, remote = sftp.active_ciphers
            assert local in ('aes256-ctr', 'aes192-ctr')
            assert remote in ('aes256-ctr', 'aes192-ctr')
            assert sftp.listdir() == ['pub', 'read.me']
    config.unlink()


def test_connection_with_config_identity(sftpserver):
    '''connect to a public sftp server using an OpenSSH config identity'''
    config = Path(f'{USER_HOME}/.ssh/config')
    config.parent.mkdir(exist_ok=True, mode=0o700)
    config.touch(exist_ok=True, mode=0o644)
    config.write_bytes(bytes(('Host 127.0.0.1\n\t'
                              'IdentityFile id_sftpretty\n\t'
                              f'User {USER}').encode('utf-8')))
    cnopts = CnOpts(config=config.as_posix(), knownhosts='sftpserver.pub')
    with sftpserver.serve_content(VFS):
        params = conn(sftpserver)
        params['cnopts'] = cnopts
        del params['private_key']
        del params['username']
        with Connection(**params) as sftp:
            assert sftp.listdir() == ['pub', 'read.me']
    config.unlink()
