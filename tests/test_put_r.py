'''test sftpretty.put_r'''

import pytest

from blddirs import build_dir_struct
from common import rmdir
from pathlib import Path
from tempfile import mkdtemp


def test_put_r(lsftp):
    '''test put_r'''
    localpath = Path(mkdtemp()).as_posix()
    remote = Path.home()
    build_dir_struct(localpath)
    local = Path(localpath).joinpath('pub')
    lsftp.put_r(local.as_posix(), remote.as_posix())

    rmdir(localpath)


# TODO
# def test_put_r_ro(psftp):
#     '''test put_r failure on remote read-only srvr'''
#     # run the op
#     with pytest.raises(IOError):
#         psftp.put_r('.', '.')


def test_put_r_bad_local(lsftp):
    '''test put_r failure on non-existing local directory'''
    # run the op
    with pytest.raises(OSError):
        lsftp.put_r('/non-existing', '.')
