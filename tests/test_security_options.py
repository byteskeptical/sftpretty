'''test sftpretty.compression param'''

from common import SKIP_IF_CI


@SKIP_IF_CI
def test_security_options(lsftp):
    '''test the security_options property has expected attributes and that
    they are tuples'''
    secopts = lsftp.security_options
    for attr in ['ciphers', 'compression', 'digests', 'kex', 'key_types']:
        print(attr)
        assert hasattr(secopts, attr)
        assert isinstance(getattr(secopts, attr), tuple)
