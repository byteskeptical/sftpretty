'''test sftpretty.compression param'''

from common import LOCAL, SKIP_IF_CI
from sftpretty import CnOpts, Connection


def test_compression_default():
    '''test that a default connection does not have compression enabled'''
    with Connection(**LOCAL) as sftp:
        assert sftp.active_compression == ('none', 'none')


@SKIP_IF_CI
def test_compression_enabled():
    '''test that compress=True results in compression enabled, assuming
    that the server supports compression'''
    copts = LOCAL.copy()
    cnopts = CnOpts(knownhosts=None)
    cnopts.compress = True
    copts['cnopts'] = cnopts
    with Connection(**copts) as sftp:
        lcompress, rcompress = sftp.active_compression
        assert lcompress != 'none'
        assert rcompress != 'none'
