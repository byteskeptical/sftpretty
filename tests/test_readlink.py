'''test sftpretty.readlink'''

from io import BytesIO
from pathlib import Path


def test_readlink(lsftp):
    '''test the readlink method'''
    buf = b'I will not buy this record, it is scratched\nMy hovercraft'\
          b' is full of eels.'
    flo = BytesIO(buf)
    rfile = 'readme.txt'
    rlink = 'readme.sym'
    rpath = Path.home().joinpath(rfile).as_posix()
    lsftp.putfo(flo, rfile)
    lsftp.symlink(rfile, rlink)

    result = lsftp.readlink(rlink).endswith(rpath)
    lsftp.remove(rlink)
    lsftp.remove(rfile)
    # test assert after cleanup
    assert result
