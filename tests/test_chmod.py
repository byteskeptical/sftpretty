'''test sftpretty.chmod'''

import pytest

from common import conn, SKIP_IF_CI, tempfile_containing, VFS
from pathlib import Path
from sftpretty import Connection, st_mode_to_int


def test_chmod_not_exist(sftpserver):
    '''verify error if trying to chmod something that isn't there'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as psftp:
            with pytest.raises(IOError):
                psftp.chmod('i-do-not-exist.txt', 666)


@SKIP_IF_CI
def test_chmod_simple(lsftp):
    '''test basic chmod with octal mode represented by an int'''
    new_mode = 744      # user=rwx g=r o=r
    with tempfile_containing(contents='') as fname:
        base_fname = Path(fname).name
        org_attrs = lsftp.put(fname)
        lsftp.chmod(base_fname, new_mode)
        new_attrs = lsftp.stat(base_fname)
        lsftp.remove(base_fname)
    # that the new mod 744 is as we wanted
    assert st_mode_to_int(new_attrs.st_mode) == new_mode
    # that we actually changed something
    assert new_attrs.st_mode != org_attrs.st_mode


# TODO
# def test_chmod_fail_ro(psftp):
#     '''test chmod against read-only server'''
#     new_mode = 440
#     fname = 'readme.txt'
#     with pytest.raises(IOError):
#         psftp.chmod(fname, new_mode)
