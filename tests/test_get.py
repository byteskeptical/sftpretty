'''test sftpretty.get'''

import pytest

from common import conn, VFS
from pathlib import Path
from sftpretty import Connection
from unittest.mock import Mock


def test_get(sftpserver, tempfile_containing):
    '''download a file'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo1')
            localfile = tempfile_containing(contents='')
            sftp.get('foo1.txt', localfile)

            assert open(localfile, 'rb').read() == b'content of foo1.txt'


def test_get_bad_remote(sftpserver, tempfile_containing):
    '''download a file but it does not exist'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo1')
            localfile = tempfile_containing(contents='')
            with pytest.raises(IOError):
                sftp.get('readme-not-there.txt', localfile)

                assert open(localfile, 'rb').read()[0:7] != b'Welcome'


def test_get_callback(sftpserver, tempfile_containing):
    '''test .get callback'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo1')
            cback = Mock(return_value=None)
            localfile = tempfile_containing(contents='')
            result = sftp.get('foo1.txt', localfile, callback=cback)

            assert open(localfile, 'rb').read() == b'content of foo1.txt'
            # verify callback was called
            assert cback.call_count
            # unlike .put() nothing is returned from the operation
            assert result is None


def test_get_glob_fails(sftpserver, tempfile_containing):
    '''try and use get a file with a pattern - Fails'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo1')
            localfile = tempfile_containing(contents='')
            with pytest.raises(IOError):
                sftp.get('*', localfile)


def test_get_preserve_mtime(sftpserver, tempfile_containing):
    '''test that m_time is preserved from local to remote, when get'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo1')
            remotefile = 'foo1.txt'
            r_stat = sftp.stat(remotefile)
            localfile = tempfile_containing(contents='')
            sftp.get(remotefile, localfile, preserve_mtime=True)

            assert r_stat.st_mtime == Path(localfile).stat().st_mtime


def test_get_resume(sftpserver, tempfile_containing):
    '''test that resume continues partial download when it exists'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo1')
            remotesize = sftp.stat('foo1.txt').st_size
            localfile = tempfile_containing(contents='content of')
            localsize = Path(localfile).stat().st_size
            sftp.get('foo1.txt', localfile, resume=True)

            assert open(localfile, 'rb').read() == b'content of foo1.txt'
            # verify difference between remotesize and partial localsize
            assert 9 == (remotesize - localsize)
