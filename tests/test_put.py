'''test sftpretty.put'''

import pytest

from common import conn, SKIP_IF_CI, tempfile_containing, VFS
from pathlib import Path
from sftpretty import Connection
from time import sleep
from unittest.mock import Mock


@SKIP_IF_CI
def test_put_callback(lsftp):
    '''test the callback feature of put'''
    cback = Mock(return_value=None)
    with tempfile_containing() as fname:
        base_fname = Path(fname).name
        lsftp.chdir('/home/test')
        lsftp.put(fname, callback=cback)
        # clean up
        lsftp.remove(base_fname)
    # verify callback was called
    assert cback.call_count


@SKIP_IF_CI
def test_put_confirm(lsftp):
    '''test the confirm feature of put'''
    with tempfile_containing() as fname:
        base_fname = Path(fname).name
        lsftp.chdir('/home/test')
        result = lsftp.put(fname)
        # clean up
        lsftp.remove(base_fname)
    # verify that an SFTPAttribute like Path.stat() was returned
    assert result.st_size == 8192
    assert result.st_uid is not None
    assert result.st_gid is not None
    assert result.st_atime
    assert result.st_mtime


@SKIP_IF_CI
def test_put(lsftp):
    '''run test on localhost'''
    contents = 'now is the time\nfor all good...'
    with tempfile_containing(contents=contents) as fname:
        base_fname = Path(fname).name
        if base_fname in lsftp.listdir():
            lsftp.remove(base_fname)
        assert base_fname not in lsftp.listdir()
        lsftp.put(fname)
        assert base_fname in lsftp.listdir()
        with tempfile_containing(contents='') as tfile:
            lsftp.get(base_fname, tfile)
            assert open(tfile).read() == contents
        # clean up
        lsftp.remove(base_fname)


def test_put_bad_local(sftpserver):
    '''try to put a non-existing file to a read-only server'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            with tempfile_containing() as fname:
                pass
            # tempfile has been removed
            with pytest.raises(OSError):
                sftp.put(fname)


# TODO
# def test_put_not_allowed(psftp):
#     '''try to put a file to a read-only server'''
#     with tempfile_containing() as fname:
#         with pytest.raises(IOError):
#             psftp.put(fname)


@SKIP_IF_CI
def test_put_preserve_mtime(lsftp):
    '''test that m_time is preserved from local to remote, when put'''
    with tempfile_containing() as fname:
        base_fname = Path(fname).name
        base = Path(fname).stat()
        # with Connection(**SFTP_LOCAL) as sftp:
        result1 = lsftp.put(fname, preserve_mtime=True)
        sleep(2)
        result2 = lsftp.put(fname, preserve_mtime=True)
        # clean up
        lsftp.remove(base_fname)
    # see if times are modified
    # assert base.st_atime == result1.st_atime
    assert int(base.st_mtime) == result1.st_mtime
    # assert result1.st_atime == result2.st_atime
    assert int(result1.st_mtime) == result2.st_mtime
