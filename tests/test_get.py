'''test sftpretty.get'''

import pytest

from common import conn, tempfile_containing, VFS
from pathlib import Path
from sftpretty import Connection
from unittest.mock import Mock


def test_get(sftpserver):
    '''download a file'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as psftp:
            psftp.chdir('pub/foo1')
            with tempfile_containing(contents='') as fname:
                psftp.get('foo1.txt', fname)
                assert open(fname, 'rb').read() == b'content of foo1.txt'


def test_get_callback(sftpserver):
    '''test .get callback'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as psftp:
            psftp.chdir('pub/foo1')
            cback = Mock(return_value=None)
            with tempfile_containing(contents='') as fname:
                result = psftp.get('foo1.txt', fname, callback=cback)
                assert open(fname, 'rb').read() == b'content of foo1.txt'
            # verify callback was called
            assert cback.call_count
            # unlike .put() nothing is returned from the operation
            assert result is None


def test_get_bad_remote(sftpserver):
    '''download a file'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as psftp:
            psftp.chdir('pub/foo1')
            with tempfile_containing(contents='') as fname:
                with pytest.raises(IOError):
                    psftp.get('readme-not-there.txt', fname)
                assert open(fname, 'rb').read()[0:7] != b'Welcome'


def test_get_preserve_mtime(sftpserver):
    '''test that m_time is preserved from local to remote, when get'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as psftp:
            psftp.chdir('pub/foo1')
            remotefile = 'foo1.txt'
            r_stat = psftp.stat(remotefile)
            with tempfile_containing(contents='') as localfile:
                psftp.get(remotefile, localfile, preserve_mtime=True)
                assert r_stat.st_mtime == Path(localfile).stat().st_mtime


def test_get_glob_fails(sftpserver):
    '''try and use get a file with a pattern - Fails'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as psftp:
            psftp.chdir('pub/foo1')
            with tempfile_containing(contents='') as fname:
                with pytest.raises(IOError):
                    psftp.get('*', fname)
