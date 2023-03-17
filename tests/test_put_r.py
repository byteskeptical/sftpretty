'''test sftpretty.put_r'''

import pytest

from blddirs import build_dir_struct
from pathlib import Path
from tempfile import mkdtemp


def test_put_r(lsftp):
    '''test put_r'''
    localpath = mkdtemp()
    remote = Path.home().as_posix()
    build_dir_struct(localpath)
    local = Path(localpath).joinpath('pub').as_posix()
    # run the op
    lsftp.put_r(local, remote)

    # inspect results

    # cleanup remote
    lsftp.rmdir(Path(remote).joinpath(Path(localpath).stem).as_posix())

    # cleanup local
    Path(localpath).rmdir()

    # check results


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
