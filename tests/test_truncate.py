'''test sftpretty.listdir'''

from common import STARS8192
from io import BytesIO


def test_truncate_smaller(lsftp):
    '''test truncate, make file smaller'''
    flo = BytesIO(bytes(STARS8192, 'UTF-8'))
    rname = 'truncate.txt'
    try:
        lsftp.remove(rname)
    except IOError:
        pass
    lsftp.putfo(flo, rname)
    new_size = lsftp.truncate(rname, 4096)
    assert new_size == 4096
    lsftp.remove(rname)


def test_truncate_larger(lsftp):
    '''test truncate, make file larger'''
    flo = BytesIO(bytes(STARS8192, 'UTF-8'))
    rname = 'truncate.txt'
    try:
        lsftp.remove(rname)
    except IOError:
        pass
    lsftp.putfo(flo, rname)
    new_size = lsftp.truncate(rname, 2 * 8192)
    assert new_size == 2 * 8192
    lsftp.remove(rname)


def test_truncate_same(lsftp):
    '''test truncate, make file same size'''
    flo = BytesIO(bytes(STARS8192, 'UTF-8'))
    rname = 'truncate.txt'
    try:
        lsftp.remove(rname)
    except IOError:
        pass
    lsftp.putfo(flo, rname)
    new_size = lsftp.truncate(rname, 8192)
    assert new_size == 8192
    lsftp.remove(rname)


# TODO
# def test_truncate_ro(psftp):
#     '''test truncate, against read-only server'''
#     rname = Path.home().joinpath('readme.txt').as_posix()
#     with pytest.raises(IOError):
#         _ = psftp.truncate(rname, 8192)
