'''test sftpretty.remove and sftpretty.unlink methods'''

import pytest

from common import SKIP_IF_ROOT, SKIP_IF_WIN
from pathlib import Path


def test_remove(lsftp, remote_tmpdir, tempfile_containing):
    '''test the remove method'''
    localfile = tempfile_containing()
    base_fname = Path(localfile).name
    rfile = Path(remote_tmpdir).joinpath(base_fname).as_posix()
    lsftp.put(localfile, rfile)
    is_there = base_fname in lsftp.listdir(remote_tmpdir)
    lsftp.remove(rfile)
    not_there = base_fname not in lsftp.listdir(remote_tmpdir)

    assert is_there
    assert not_there


def test_remove_does_not_exist(lsftp, remote_tmpdir):
    '''test remove against a non-existant file'''
    rfile = Path(remote_tmpdir).joinpath('i-am-not-here.txt').as_posix()
    with pytest.raises(IOError):
        lsftp.remove(rfile)


@SKIP_IF_ROOT
@SKIP_IF_WIN  # Win32-OpenSSH doesn't translate mode bits into ACLs
def test_remove_ro(lsftp, remote_tmpdir, tempfile_containing):
    '''test remove against read-only server'''
    localfile = tempfile_containing()
    remotedir = Path(remote_tmpdir).joinpath('readonly')
    remotefile = remotedir.joinpath(Path(localfile).name)
    lsftp.mkdir_p(remotedir.as_posix())
    lsftp.put(localfile, remotefile.as_posix())
    lsftp.chmod(remotedir.as_posix(), 500)
    try:
        with pytest.raises(PermissionError):
            lsftp.remove(remotefile.as_posix())
    finally:
        lsftp.chmod(remotedir.as_posix(), 700)
