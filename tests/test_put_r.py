'''test sftpretty.put_r'''

import pytest

from blddirs import build_dir_struct


def test_put_r(lsftp, remote_tmpdir, tmp_path):
    '''test put_r'''
    build_dir_struct(tmp_path.as_posix())
    local = tmp_path.joinpath('pub').as_posix()
    lsftp.put_r(local, remote_tmpdir)

    assert lsftp.listdir(remote_tmpdir) != []


# TODO
# def test_put_r_ro(lsftp):
#     '''test put_r failure on remote read-only server'''
#     with pytest.raises(IOError):
#         lsftp.put_r('.', '.')


def test_put_r_bad_local(lsftp, remote_tmpdir):
    '''test put_r failure on non-existing local directory'''
    with pytest.raises(OSError):
        lsftp.put_r('/non-existing', remote_tmpdir)
