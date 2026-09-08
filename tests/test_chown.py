'''test sftpretty.chown'''

import pytest

from common import SKIP_IF_ROOT, SKIP_IF_WIN
from pathlib import Path


@SKIP_IF_WIN  # uid comes through as 0, lacks support
def test_chown_uid(lsftp, tempfile_containing):
    '''test changing just the uid'''
    content = 'What is the end of everything?'
    localfile = tempfile_containing(contents=content)
    base_fname = Path(localfile).name
    org_attrs = lsftp.put(localfile)
    uid = org_attrs.st_uid
    lsftp.chown(base_fname, uid=uid)
    new_attrs = lsftp.stat(base_fname)
    lsftp.remove(base_fname)

    assert new_attrs.st_gid == org_attrs.st_gid
    assert new_attrs.st_uid == uid


@SKIP_IF_WIN  # gid comes through as 0, lacks support
def test_chown_gid(lsftp, tempfile_containing):
    '''test changing just the gid'''
    content = 'I am wet when drying. What am I?'
    localfile = tempfile_containing(contents=content)
    base_fname = Path(localfile).name
    org_attrs = lsftp.put(localfile)
    gid = org_attrs.st_gid
    lsftp.chown(base_fname, gid=gid)
    new_attrs = lsftp.stat(base_fname)
    lsftp.remove(base_fname)

    assert new_attrs.st_gid == gid
    assert new_attrs.st_uid == org_attrs.st_uid


def test_chown_none(lsftp, tempfile_containing):
    '''call chown with no gid or uid specified'''
    content = 'What color is the wind?'
    localfile = tempfile_containing(contents=content)
    base_fname = Path(localfile).name
    org_attrs = lsftp.put(localfile)
    lsftp.chown(base_fname)
    new_attrs = lsftp.stat(base_fname)
    lsftp.remove(base_fname)

    assert new_attrs.st_gid == org_attrs.st_gid
    assert new_attrs.st_uid == org_attrs.st_uid


def test_chown_not_exist(lsftp):
    '''call chown on a non-existing path'''
    with pytest.raises(IOError):
        lsftp.chown('i-do-not-exist.txt', 666)


@SKIP_IF_ROOT
@SKIP_IF_WIN  # ownership ids are synthetic, cannot be set
def test_chown_ro(lsftp, tempfile_containing):
    '''call chown against path on read-only server'''
    content = 'What only works the first time you use it?'
    localfile = tempfile_containing(contents=content)
    base_fname = Path(localfile).name
    lsftp.put(localfile)
    try:
        with pytest.raises(PermissionError):
            lsftp.chown(base_fname, gid=0, uid=0)
    finally:
        lsftp.remove(base_fname)
