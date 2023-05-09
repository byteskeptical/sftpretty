'''test sftpretty.put_d'''

import pytest

from blddirs import build_dir_struct
from common import rmdir
from pathlib import Path
from tempfile import mkdtemp


def test_put_d(lsftp):
    '''test put_d'''
    localpath = Path(mkdtemp()).as_posix()
    remote = Path.home()
    build_dir_struct(localpath)
    local = Path(localpath).joinpath('pub')
    lsftp.put_d(local.as_posix(), remote.as_posix())

    rmdir(localpath)


# TODO
# def test_put_d_ro(psftp):
#     '''test put_d failure on remote read-only srvr'''
#     # run the op
#     with pytest.raises(IOError):
#         psftp.put_d('.', '.')


def test_put_d_bad_local(lsftp):
    '''test put_d failure on non-existing local directory'''
    # run the op
    with pytest.raises(OSError):
        lsftp.put_d('/non-existing', '.')
