'''test sftpretty.putfo'''

from io import BytesIO
from unittest.mock import call, Mock


def test_putfo_callback_fsize(lsftp):
    '''test putfo with callback and file_size'''
    rfile = 'a-test-file'
    buf = (b'I will not buy this record, it is scratched\nMy hovercraft '
           b'is full of eels.')
    fsize = len(buf)
    bwrote = fsize - 3
    flo = BytesIO(buf)
    cback = Mock(return_value=None)
    lsftp.putfo(flo, rfile, file_size=bwrote, callback=cback)
    lsftp.remove(rfile)
    assert cback.call_count
    assert cback.call_args_list == [call(fsize, bwrote)]


def test_putfo_callback(lsftp):
    '''test putfo with callback'''
    rfile = 'a-test-file'
    buf = (b'I will not buy this record, it is scratched\nMy hovercraft '
           b'is full of eels.')
    fsize = len(buf)
    flo = BytesIO(buf)
    cback = Mock(return_value=None)
    lsftp.putfo(flo, rfile, callback=cback)
    lsftp.remove(rfile)
    assert cback.call_count
    assert cback.call_args_list == [call(fsize, fsize)]


def test_putfo_flo(lsftp):
    '''test putfo in simple form'''
    rfile = 'a-test-file'
    buf = b'I will not buy this record, it is scratched\nMy hovercraft'\
          b' is full of eels.'
    flo = BytesIO(buf)
    assert rfile not in lsftp.listdir()
    rslt = lsftp.putfo(flo, rfile)
    assert rfile in lsftp.listdir()
    lsftp.remove(rfile)
    assert rslt.st_size == len(buf)


def test_putfo_no_remotepath(lsftp):
    '''test putfo uses uuid fallback when not specifying a remotepath'''
    buf = b'I will not buy this record, it is scratched\nMy hovercraft'\
          b' is full of eels.'
    flo = BytesIO(buf)
    rslt = lsftp.putfo(flo)
    assert rslt.st_size == len(buf)


# TODO
# def test_putfo_ro_srv(psftp):
#     '''test error returned from attempting to putfo to a read-only server'''
#     buf = b'I will not buy this record, it is scratched\nMy hovercraft'\
#           b' is full of eels.'
#     flo = BytesIO(buf)
#     with pytest.raises(TypeError):
#         psftp.putfo(flo)
