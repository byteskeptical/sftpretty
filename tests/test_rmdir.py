'''test sftpretty.rmdir'''

import pytest

from common import SKIP_IF_ROOT, SKIP_IF_WIN
from pathlib import Path


def test_rmdir(lsftp, remote_tmpdir):
    '''test mkdir'''
    dirname = 'test-rm'
    remotedir = Path(remote_tmpdir).joinpath(dirname).as_posix()
    lsftp.mkdir(remotedir)
    assert dirname in lsftp.listdir(remote_tmpdir)
    lsftp.rmdir(remotedir)
    assert dirname not in lsftp.listdir(remote_tmpdir)


@SKIP_IF_ROOT
@SKIP_IF_WIN  # Win32-OpenSSH doesn't translate mode bits into ACLs
def test_rmdir_ro(lsftp, remote_tmpdir):
    '''test rmdir against read-only server'''
    parent = Path(remote_tmpdir).joinpath('readonly')
    remotedir = parent.joinpath('test-rm')
    lsftp.mkdir_p(remotedir.as_posix())
    lsftp.chmod(parent.as_posix(), 500)
    try:
        with pytest.raises(PermissionError):
            lsftp.rmdir(remotedir.as_posix())
    finally:
        lsftp.chmod(parent.as_posix(), 700)
