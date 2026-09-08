'''test sftpretty.put'''

import pytest

from common import conn, SKIP_IF_ROOT, SKIP_IF_WIN, VFS
from pathlib import Path
from sftpretty import Connection
from time import sleep
from unittest.mock import Mock


def test_put(lsftp, tempfile_containing):
    '''test upload to localhost'''
    content = 'now is the time\nfor all good...'
    localfile = tempfile_containing(contents=content)
    localfileZ = tempfile_containing(contents='')
    base_fname = Path(localfile).name
    if base_fname in lsftp.listdir():
        lsftp.remove(base_fname)

    assert base_fname not in lsftp.listdir()

    lsftp.put(localfile)
    assert base_fname in lsftp.listdir()

    lsftp.get(base_fname, localfileZ)
    assert open(localfileZ).read() == content

    # clean up
    lsftp.remove(base_fname)


def test_put_bad_local(sftpserver, tempfile_containing):
    '''try to put a non-existing file to a read-only server'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            localfile = tempfile_containing()
            Path(localfile).unlink()
            # tempfile has been removed
            with pytest.raises(OSError):
                sftp.put(localfile)


def test_put_callback(lsftp, tempfile_containing):
    '''test the callback feature of put'''
    cback = Mock(return_value=None)
    localfile = tempfile_containing()
    base_fname = Path(localfile).name
    lsftp.chdir(Path.home().as_posix())
    lsftp.put(localfile, callback=cback)
    # clean up
    lsftp.remove(base_fname)

    # verify callback was called
    assert cback.call_count


def test_put_confirm(lsftp, tempfile_containing):
    '''test the confirm feature of put'''
    localfile = tempfile_containing()
    base_fname = Path(localfile).name
    lsftp.chdir(Path.home().as_posix())
    result = lsftp.put(localfile)
    # clean up
    lsftp.remove(base_fname)

    # verify that an SFTPAttribute like Path.stat() was returned
    assert result.st_size == 8192
    assert result.st_uid is not None
    assert result.st_gid is not None
    assert result.st_atime
    assert result.st_mtime


def test_put_preserve_mtime(lsftp, tempfile_containing):
    '''test that m_time is preserved from local to remote, when put'''
    localfile = tempfile_containing()
    base_fname = Path(localfile).name
    base = Path(localfile).stat()
    # with Connection(**LOCAL) as sftp:
    result1 = lsftp.put(localfile, preserve_mtime=True)
    sleep(2)
    result2 = lsftp.put(localfile, preserve_mtime=True)
    # clean up
    lsftp.remove(base_fname)

    # see if times are modified
    # assert base.st_atime == result1.st_atime
    assert int(base.st_mtime) == result1.st_mtime
    # assert result1.st_atime == result2.st_atime
    assert int(result1.st_mtime) == result2.st_mtime


def test_put_resume(lsftp, tempfile_containing):
    '''test upload resume feature'''
    localfile = tempfile_containing(contents='resume this...')
    localfileZ = tempfile_containing(contents='resume ')
    base = Path(localfile).stat()
    partial = lsftp.put(localfileZ)
    with open(localfileZ, 'ab') as fh:
        fh.write('this...'.encode('utf-8'))
    result = lsftp.put(localfileZ, preserve_mtime=True, resume=True)

    assert base.st_size == result.st_size
    assert partial.st_mtime == result.st_mtime


@SKIP_IF_ROOT
@SKIP_IF_WIN  # Win32-OpenSSH doesn't translate mode bits into ACLs
def test_put_ro(lsftp, remote_tmpdir, tempfile_containing):
    '''try to put a file on a read-only server'''
    localfile = tempfile_containing()
    remotedir = Path(remote_tmpdir).joinpath('readonly')
    remotefile = remotedir.joinpath(Path(localfile).name)
    lsftp.mkdir_p(remotedir.as_posix())
    lsftp.chmod(remotedir.as_posix(), 500)
    try:
        with pytest.raises(PermissionError):
            lsftp.put(localfile, remotefile.as_posix())
    finally:
        lsftp.chmod(remotedir.as_posix(), 700)
