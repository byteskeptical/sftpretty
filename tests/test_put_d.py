'''test sftpretty.put_d'''

import pytest

from blddirs import build_dir_struct
from common import SKIP_IF_CI
from pathlib import Path
from tempfile import mkdtemp


# TODO 1
@SKIP_IF_CI
def test_put_d(lsftp):
    '''test put_d'''
    localpath = mkdtemp()
    print(localpath)
    remote_dir = Path(localpath).stem
    build_dir_struct(localpath)
    localpath = Path(localpath).joinpath('pub').as_posix()
    print(localpath)
    # run the op
    lsftp.put_d(localpath, remote_dir)

    # inspect results

    # cleanup remote
    lsftp.rmdir(remote_dir)

    # cleanup local
    Path(localpath).rmdir()

    # check results


# TODO
# def test_put_d_ro(psftp):
#     '''test put_d failure on remote read-only srvr'''
#     # run the op
#     with pytest.raises(IOError):
#         psftp.put_d('.', '.')


@SKIP_IF_CI
def test_put_d_bad_local(lsftp):
    '''test put_d failure on non-existing local directory'''
    # run the op
    with pytest.raises(OSError):
        lsftp.put_d('/non-existing', '.')
