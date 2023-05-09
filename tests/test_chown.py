'''test sftpretty.chown'''

import pytest

from common import SKIP_IF_WIN, tempfile_containing
from pathlib import Path


@SKIP_IF_WIN  # uid comes through as 0, lacks support
def test_chown_uid(lsftp):
    '''test changing just the uid'''
    with tempfile_containing() as fname:
        base_fname = Path(fname).name
        org_attrs = lsftp.put(fname)
        uid = org_attrs.st_uid
        lsftp.chown(base_fname, uid=uid)
        new_attrs = lsftp.stat(base_fname)
        lsftp.remove(base_fname)
    assert new_attrs.st_gid == org_attrs.st_gid
    assert new_attrs.st_uid == uid


@SKIP_IF_WIN  # gid comes through as 0, lacks support
def test_chown_gid(lsftp):
    '''test changing just the gid'''
    with tempfile_containing() as fname:
        base_fname = Path(fname).name
        org_attrs = lsftp.put(fname)
        gid = org_attrs.st_gid
        lsftp.chown(base_fname, gid=gid)
        new_attrs = lsftp.stat(base_fname)
        lsftp.remove(base_fname)
    assert new_attrs.st_gid == gid
    assert new_attrs.st_uid == org_attrs.st_uid


def test_chown_none(lsftp):
    '''call .chown with no gid or uid specified'''
    with tempfile_containing() as fname:
        base_fname = Path(fname).name
        org_attrs = lsftp.put(fname)
        lsftp.chown(base_fname)
        new_attrs = lsftp.stat(base_fname)
        lsftp.remove(base_fname)
    assert new_attrs.st_gid == org_attrs.st_gid
    assert new_attrs.st_uid == org_attrs.st_uid


def test_chown_not_exist(lsftp):
    '''call .chown on a non-existing path'''
    with pytest.raises(IOError):
        lsftp.chown('i-do-not-exist.txt', 666)


# TODO
# def test_chown_ro_server(psftp):
#     '''call .chown against path on read-only server'''
#     with pytest.raises(IOError):
#         psftp.chown('readme.txt', gid=1000, uid=1000)
