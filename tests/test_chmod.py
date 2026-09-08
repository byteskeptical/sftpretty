'''test sftpretty.chmod'''

import pytest

from common import conn, SKIP_IF_ROOT, SKIP_IF_WIN, VFS
from pathlib import Path
from sftpretty import Connection
from sftpretty.helpers import st_mode_to_int


def test_chmod_not_exist(sftpserver):
    '''verify error if trying to chmod something that isn't there'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            with pytest.raises(IOError):
                sftp.chmod('i-do-not-exist.txt', 666)


@SKIP_IF_ROOT
@SKIP_IF_WIN  # Win32-OpenSSH doesn't translate mode bits into ACLs
def test_chmod_ro(lsftp, remote_tmpdir, tempfile_containing):
    '''test chmod against read-only path'''
    content = 'You answer me, although I never ask you questions, what am I?'
    parent = Path(remote_tmpdir).joinpath('readonly')
    rfile = parent.joinpath('readme.txt')
    lsftp.mkdir_p(parent.as_posix())
    localfile = tempfile_containing(contents=content)
    lsftp.put(localfile, rfile.as_posix())
    lsftp.chmod(parent.as_posix(), 400)  # no search bit, 500 fails
    try:
        with pytest.raises(PermissionError):
            lsftp.chmod(rfile.as_posix(), 440)
    finally:
        lsftp.chmod(parent.as_posix(), 700)


@SKIP_IF_WIN  # Win32-OpenSSH doesn't translate mode bits into ACLs
def test_chmod_simple(lsftp, tempfile_containing):
    '''test basic chmod with octal mode represented by an int'''
    content = 'Which three letters can frighten a thief away?'
    new_mode = 711
    localfile = tempfile_containing(contents=content)
    base_fname = Path(localfile).name
    org_attrs = lsftp.put(localfile)
    lsftp.chmod(base_fname, new_mode)
    new_attrs = lsftp.stat(base_fname)
    lsftp.remove(base_fname)

    assert st_mode_to_int(new_attrs.st_mode) == new_mode
    assert new_attrs.st_mode != org_attrs.st_mode
