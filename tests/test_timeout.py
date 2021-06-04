'''test sftpretty.timeout'''

from common import SKIP_IF_CI


@SKIP_IF_CI
def test_timeout_getter(lsftp):
    '''test getting the timeout value'''
    # always starts at no timeout,
    assert lsftp.timeout is None


@SKIP_IF_CI
def test_timeout_setter(lsftp):
    '''test setting the timeout value'''
    lsftp.timeout = 10.5
    assert lsftp.timeout == 10.5
    lsftp.timeout = None
    assert lsftp.timeout is None
