'''test sftpretty.remove and sftpretty.unlink methods'''

import pytest

from common import tempfile_containing
from pathlib import Path


def test_remove(lsftp, remote_tmpdir):
    '''test the remove method'''
    with tempfile_containing() as fname:
        base_fname = Path(fname).name
        rfile = Path(remote_tmpdir).joinpath(base_fname).as_posix()
        lsftp.put(fname, rfile)
        is_there = base_fname in lsftp.listdir(remote_tmpdir)
        lsftp.remove(rfile)
        not_there = base_fname not in lsftp.listdir(remote_tmpdir)

    assert is_there
    assert not_there


# TODO
# def test_remove_roserver(lsftp, remote_tmpdir):
#     '''test reaction of attempting remove on read-only server'''
#     rfile = Path(remote_tmpdir).joinpath('readme.txt').as_posix()
#     with pytest.raises(IOError):
#         lsftp.remove(rfile)


def test_remove_does_not_exist(lsftp, remote_tmpdir):
    '''test remove against a non-existant file'''
    rfile = Path(remote_tmpdir).joinpath('i-am-not-here.txt').as_posix()
    with pytest.raises(IOError):
        lsftp.remove(rfile)
