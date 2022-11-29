'''test sftpretty.put_r'''

import pytest

from blddirs import build_dir_struct
from common import SKIP_IF_CI
from pathlib import Path
from tempfile import mkdtemp


# TODO 2
@SKIP_IF_CI
def test_put_r(lsftp):
    '''test put_r'''
    localpath = mkdtemp()
    print(localpath)
    remote_dir = Path(localpath).stem
    build_dir_struct(localpath)
    localpath = Path(localpath).joinpath('pub').as_posix()
    print(localpath)
    # run the op
    lsftp.put_r(localpath, remote_dir)

    # inspect results

    # cleanup remote
    lsftp.rmdir(remote_dir)

    # cleanup local
    Path(Path(localpath).parent.as_posix()).rmdir()

    # check results


# TODO
# def test_put_r_ro(psftp):
#     '''test put_r failure on remote read-only srvr'''
#     # run the op
#     with pytest.raises(IOError):
#         psftp.put_r('.', '.')


@SKIP_IF_CI
def test_put_r_bad_local(lsftp):
    '''test put_r failure on non-existing local directory'''
    # run the op
    with pytest.raises(OSError):
        lsftp.put_r('/non-existing', '.')
