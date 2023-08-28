'''test sftpretty.get'''

import pytest

from common import conn, tempfile_containing, VFS
from pathlib import Path
from sftpretty import Connection
from unittest.mock import Mock


def test_get(sftpserver):
    '''download a file'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo1')
            with tempfile_containing(contents='') as fname:
                sftp.get('foo1.txt', fname)
                assert open(fname, 'rb').read() == b'content of foo1.txt'


def test_get_bad_remote(sftpserver):
    '''download a file but it does not exist'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo1')
            with tempfile_containing(contents='') as fname:
                with pytest.raises(IOError):
                    sftp.get('readme-not-there.txt', fname)
                assert open(fname, 'rb').read()[0:7] != b'Welcome'


def test_get_callback(sftpserver):
    '''test .get callback'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo1')
            cback = Mock(return_value=None)
            with tempfile_containing(contents='') as fname:
                result = sftp.get('foo1.txt', fname, callback=cback)
                assert open(fname, 'rb').read() == b'content of foo1.txt'
            # verify callback was called
            assert cback.call_count
            # unlike .put() nothing is returned from the operation
            assert result is None


def test_get_glob_fails(sftpserver):
    '''try and use get a file with a pattern - Fails'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo1')
            with tempfile_containing(contents='') as fname:
                with pytest.raises(IOError):
                    sftp.get('*', fname)


def test_get_preserve_mtime(sftpserver):
    '''test that m_time is preserved from local to remote, when get'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo1')
            remotefile = 'foo1.txt'
            r_stat = sftp.stat(remotefile)
            with tempfile_containing(contents='') as localfile:
                sftp.get(remotefile, localfile, preserve_mtime=True)
                assert r_stat.st_mtime == Path(localfile).stat().st_mtime


def test_get_resume(sftpserver):
    '''test that resume continues partial download when it exists'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo1')
            remotesize = sftp.stat('foo1.txt').st_size
            with tempfile_containing(contents='content of') as fname:
                localsize = Path(fname).stat().st_size
                sftp.get('foo1.txt', fname, resume=True)
                assert open(fname, 'rb').read() == b'content of foo1.txt'
            # verify difference between remotesize and partial localsize
            assert 9 == (remotesize - localsize)
