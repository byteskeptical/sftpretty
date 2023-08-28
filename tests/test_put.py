'''test sftpretty.put'''

import pytest

from common import conn, tempfile_containing, VFS
from pathlib import Path
from sftpretty import Connection
from time import sleep
from unittest.mock import Mock


def test_put(lsftp):
    '''test upload to localhost'''
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


def test_put_callback(lsftp):
    '''test the callback feature of put'''
    cback = Mock(return_value=None)
    with tempfile_containing() as fname:
        base_fname = Path(fname).name
        lsftp.chdir(Path.home().as_posix())
        lsftp.put(fname, callback=cback)
        # clean up
        lsftp.remove(base_fname)
    # verify callback was called
    assert cback.call_count


def test_put_confirm(lsftp):
    '''test the confirm feature of put'''
    with tempfile_containing() as fname:
        base_fname = Path(fname).name
        lsftp.chdir(Path.home().as_posix())
        result = lsftp.put(fname)
        # clean up
        lsftp.remove(base_fname)
    # verify that an SFTPAttribute like Path.stat() was returned
    assert result.st_size == 8192
    assert result.st_uid is not None
    assert result.st_gid is not None
    assert result.st_atime
    assert result.st_mtime


# TODO
# def test_put_not_allowed(psftp):
#     '''try to put a file to a read-only server'''
#     with tempfile_containing() as fname:
#         with pytest.raises(IOError):
#             psftp.put(fname)


def test_put_preserve_mtime(lsftp):
    '''test that m_time is preserved from local to remote, when put'''
    with tempfile_containing() as fname:
        base_fname = Path(fname).name
        base = Path(fname).stat()
        # with Connection(**LOCAL) as sftp:
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


def test_put_resume(lsftp):
    '''test upload resume feature'''
    with tempfile_containing(contents='resume this...') as fname:
        base = Path(fname).stat()
    with tempfile_containing(contents='resume ') as fname:
        partial = lsftp.put(fname)
        with open(fname, 'ab') as fh:
            fh.write('this...'.encode('utf-8'))
        result = lsftp.put(fname, preserve_mtime=True, resume=True)
    assert base.st_size == result.st_size
    assert partial.st_mtime == result.st_mtime
