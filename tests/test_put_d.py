'''test sftpretty.put_d'''

import pytest

from blddirs import build_dir_struct
from common import SKIP_IF_ROOT, SKIP_IF_WIN
from pathlib import Path


def test_put_d(lsftp, remote_tmpdir, tmp_path):
    '''test put_d'''
    build_dir_struct(tmp_path.as_posix())
    local = tmp_path.joinpath('pub').as_posix()
    lsftp.put_d(local, remote_tmpdir)
    remote = Path(remote_tmpdir).joinpath('pub').as_posix()

    assert lsftp.listdir(remote) == ['make.txt']


@SKIP_IF_ROOT
@SKIP_IF_WIN  # Win32-OpenSSH doesn't translate mode bits into ACLs
@pytest.mark.parametrize('refuse', ('mkdir', 'write'))
def test_put_d_ro(lsftp, refuse, remote_tmpdir, tmp_path):
    '''test put_d failure on remote read-only server'''
    build_dir_struct(tmp_path.as_posix())
    local = tmp_path.joinpath('pub').as_posix()

    if refuse == 'mkdir':
        remote = remote_tmpdir
    else:
        remote = Path(remote_tmpdir).joinpath('pub').as_posix()
        lsftp.mkdir_p(remote)

    lsftp.chmod(remote, 500)
    try:
        with pytest.raises(PermissionError):
            lsftp.put_d(local, remote_tmpdir)
    finally:
        lsftp.chmod(remote, 700)


def test_put_d_bad_local(lsftp, remote_tmpdir):
    '''test put_d failure on non-existing local directory'''
    with pytest.raises(OSError):
        lsftp.put_d('/non-existing', remote_tmpdir)
