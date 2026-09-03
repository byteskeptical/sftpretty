'''test sftpretty.readlink'''

from io import BytesIO
from pathlib import Path
from sftpretty.helpers import drivepath


def test_readlink(lsftp, remote_tmpdir):
    '''test the readlink method'''
    buf = b'I will not buy this record, it is scratched.\nMy hovercraft '\
          b'is full of eels.'
    flo = BytesIO(buf)
    rfile = Path(remote_tmpdir).joinpath('readme.txt').as_posix()
    rlink = Path(remote_tmpdir).joinpath('readme.sym').as_posix()
    lsftp.putfo(flo, rfile)
    lsftp.symlink(rfile, rlink)

    assert lsftp.readlink(rlink).endswith(drivepath(rfile))
