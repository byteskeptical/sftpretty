'''test sftpretty.put_d'''

import pytest

from blddirs import build_dir_struct
from pathlib import Path


def test_put_d(lsftp, remote_tmpdir, tmp_path):
    '''test put_d'''
    build_dir_struct(tmp_path.as_posix())
    local = tmp_path.joinpath('pub').as_posix()
    lsftp.put_d(local, remote_tmpdir)
    remote = Path(remote_tmpdir).joinpath('pub').as_posix()

    assert lsftp.listdir(remote) == ['make.txt']

# TODO
# def test_put_d_ro(lsftp):
#     '''test put_d failure on remote read-only server'''
#     with pytest.raises(IOError):
#         lsftp.put_d('.', '.')


def test_put_d_bad_local(lsftp, remote_tmpdir):
    '''test put_d failure on non-existing local directory'''
    with pytest.raises(OSError):
        lsftp.put_d('/non-existing', remote_tmpdir)
