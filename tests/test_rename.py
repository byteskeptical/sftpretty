'''test sftpretty.rename'''

import pytest

from common import SKIP_IF_ROOT, SKIP_IF_WIN
from pathlib import Path


def test_rename(lsftp, remote_tmpdir, tempfile_containing):
    '''test rename on remote'''
    content = 'now is the time\nfor all good...'
    localfile = tempfile_containing(contents=content)
    base_fname = Path(localfile).name
    alice = Path(remote_tmpdir).joinpath('alice').as_posix()
    bob = Path(remote_tmpdir).joinpath('bob').as_posix()
    remotefile = Path(remote_tmpdir).joinpath(base_fname).as_posix()

    assert base_fname not in lsftp.listdir(remote_tmpdir)

    lsftp.put(localfile, remotefile)
    lsftp.rename(remotefile, alice)
    rdirs = lsftp.listdir(remote_tmpdir)

    assert 'alice' in rdirs
    assert base_fname not in rdirs

    lsftp.rename(alice, bob, posix=False)
    rdirs = lsftp.listdir(remote_tmpdir)

    assert 'alice' not in rdirs
    assert 'bob' in rdirs

    with lsftp.open(bob) as remote:
        assert remote.read().decode() == content


@SKIP_IF_ROOT
@SKIP_IF_WIN  # Win32-OpenSSH doesn't translate mode bits into ACLs
@pytest.mark.parametrize('posix', (True, False))
def test_rename_ro(lsftp, posix, remote_tmpdir, tempfile_containing):
    '''test rename on a read-only server'''
    localfile = tempfile_containing()
    remotedir = Path(remote_tmpdir).joinpath('readonly')
    remotefile = remotedir.joinpath(Path(localfile).name)
    lsftp.mkdir_p(remotedir.as_posix())
    lsftp.put(localfile, remotefile.as_posix())
    lsftp.chmod(remotedir.as_posix(), 500)
    try:
        with pytest.raises(PermissionError):
            lsftp.rename(remotefile.as_posix(),
                         remotedir.joinpath('alice').as_posix(), posix=posix)
    finally:
        lsftp.chmod(remotedir.as_posix(), 700)
