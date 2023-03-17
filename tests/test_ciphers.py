'''test CnOpts.ciphers param'''

# these can not use fixtures as we need to set ciphers prior to the connection
# being made and fixtures are already active connections.

from common import LOCAL
from sftpretty import CnOpts, Connection


def test_connection_ciphers_cnopts():
    '''test the CnOpts.ciphers portion of the Connection'''
    ciphers = ('aes256-ctr', 'aes256-cbc')
    copts = LOCAL.copy()  # don't sully the module level variable
    cnopts = CnOpts(knownhosts=None)
    cnopts.ciphers = ciphers
    copts['cnopts'] = cnopts
    assert copts != LOCAL
    with Connection(**copts) as sftp:
        rslt = sftp.listdir()
        assert len(rslt) > 1


def test_active_ciphers():
    '''test that method returns a tuple of strings, that show ciphers used'''
    ciphers = ('aes256-ctr', 'aes256-cbc')
    copts = LOCAL.copy()  # don't sully the module level variable
    cnopts = CnOpts(knownhosts=None)
    cnopts.ciphers = ciphers
    copts['cnopts'] = cnopts
    with Connection(**copts) as sftp:
        local_cipher, remote_cipher = sftp.active_ciphers
    assert local_cipher in ciphers
    assert remote_cipher in ciphers
