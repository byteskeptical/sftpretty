'''test sftpretty.helpers.hash'''

from sftpretty.helpers import hash


def test_hash_distinguishes_different_content():
    '''different input must produce different digests -- regression test
    for a bug where hash() always returned the digest of an empty input,
    making all fingerprint comparisons succeed regardless of content'''
    assert hash('some content') != hash('some different content')
