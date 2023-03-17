'''test sftpretty.compression param'''

# pylint: disable=W0142

# these can not use fixtures as we need to set compression prior to the
# connection being made and fixtures are already active connections.

from common import LOCAL
from sftpretty import CnOpts, Connection


def test_compression_default():
    '''test that a default connection does not have compression enabled'''
    with Connection(**LOCAL) as sftp:
        assert sftp.active_compression == ('none', 'none')


def test_compression_enabled():
    '''test that compression=True results in compression enabled, assuming
    that the server supports compression'''
    copts = LOCAL.copy()
    cnopts = CnOpts(knownhosts=None)
    cnopts.compression = True
    copts['cnopts'] = cnopts
    with Connection(**copts) as sftp:
        lcompress, rcompress = sftp.active_compression
        assert lcompress != 'none'
        assert rcompress != 'none'
