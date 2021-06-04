'''test sftpretty.readlink'''

from common import SKIP_IF_CI
from io import BytesIO


@SKIP_IF_CI
def test_readlink(lsftp):
    '''test the readlink method'''
    rfile = 'readme.txt'
    rlink = 'readme.sym'
    buf = b'I will not buy this record, it is scratched\nMy hovercraft'\
          b' is full of eels.'
    flo = BytesIO(buf)
    print(lsftp.listdir())
    lsftp.putfo(flo, rfile)
    lsftp.symlink(rfile, rlink)

    result = lsftp.readlink(rlink).endswith('/home/test/readme.txt')
    lsftp.remove(rlink)
    lsftp.remove(rfile)
    # test assert after cleanup
    assert result
