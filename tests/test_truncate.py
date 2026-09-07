'''test sftpretty.listdir'''

import pytest

from common import STARS8192
from io import BytesIO
from pathlib import Path


@pytest.mark.parametrize('size', (2 * 8192, 8192, 4096),
                         ids=('larger', 'same', 'smaller'))
def test_truncate(lsftp, remote_tmpdir, size):
    '''test truncate to a larger, same and smaller size'''
    flo = BytesIO(bytes(STARS8192, 'UTF-8'))
    rname = Path(remote_tmpdir).joinpath('truncate.txt').as_posix()
    lsftp.putfo(flo, rname)

    assert lsftp.truncate(rname, size) == size


# TODO
# def test_truncate_ro(lsftp,, remote_tmpdir):
#     '''test truncate against read-only server'''
#     rfile = Path(remote_tmpdir).joinpath('readme.txt').as_posix()
#     with pytest.raises(IOError):
#         _ = lsftp.truncate(rfile, 8192)
