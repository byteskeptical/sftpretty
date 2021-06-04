'''test sftpretty.compression param'''

# pylint: disable=W0142

# these can not use fixtures as we need to set compression prior to the
# connection being made and fixtures are already active connections.

from common import SKIP_IF_CI, SFTP_LOCAL
from sftpretty import CnOpts, Connection


@SKIP_IF_CI
def test_compression_default():
    '''test that a default connection does not have compression enabled'''
    with Connection(**SFTP_LOCAL) as sftp:
        assert sftp.active_compression == ('none', 'none')


@SKIP_IF_CI
def test_compression_enabled():
    '''test that compression=True results in compression enabled, assuming
    that the server supports compression'''
    copts = SFTP_LOCAL.copy()
    cnopts = CnOpts()
    cnopts.compression = True
    copts['cnopts'] = cnopts
    with Connection(**copts) as sftp:
        lcompress, rcompress = sftp.active_compression
        assert lcompress != 'none'
        assert rcompress != 'none'
