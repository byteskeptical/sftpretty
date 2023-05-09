'''test sftpretty.chmod'''

import pytest

from common import conn, SKIP_IF_WIN, tempfile_containing, VFS
from pathlib import Path
from sftpretty import Connection
from sftpretty.helpers import st_mode_to_int


def test_chmod_not_exist(sftpserver):
    '''verify error if trying to chmod something that isn't there'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            with pytest.raises(IOError):
                sftp.chmod('i-do-not-exist.txt', 666)


@SKIP_IF_WIN
def test_chmod_simple(lsftp):
    '''test basic chmod with octal mode represented by an int'''
    new_mode = 711
    with tempfile_containing(contents='') as fname:
        base_fname = Path(fname).name
        org_attrs = lsftp.put(fname)
        lsftp.chmod(base_fname, new_mode)
        new_attrs = lsftp.stat(base_fname)
        lsftp.remove(base_fname)

    assert st_mode_to_int(new_attrs.st_mode) == new_mode
    assert new_attrs.st_mode != org_attrs.st_mode


# TODO
# def test_chmod_fail_ro(psftp):
#     '''test chmod against read-only server'''
#     new_mode = 440
#     fname = 'readme.txt'
#     with pytest.raises(IOError):
#         psftp.chmod(fname, new_mode)
