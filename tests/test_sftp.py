'''test sftpretty module'''

# psftp and lsftp fixtures are from conftest.py

from common import conn, SKIP_IF_CI, tempfile_containing, VFS
from pathlib import Path
from sftpretty import Connection
from stat import S_ISLNK


@SKIP_IF_CI
def test_sftp_client(lsftp):
    '''test for access to the underlying, active sftpclient'''
    # with Connection(**SFTP_PUBLIC) as sftp:
    #     assert 'normalize' in dir(sftp.sftp_client)
    #     assert 'readlink' in dir(sftp.sftp_client)
    assert 'normalize' in dir(lsftp.sftp_client)
    assert 'readlink' in dir(lsftp.sftp_client)


@SKIP_IF_CI
def test_mkdir_p(lsftp):
    '''test mkdir_p simple, testing 2 things, oh well'''
    rdir = 'foo/bar/baz'
    rdir2 = 'foo/bar'
    assert lsftp.exists(rdir) is False
    lsftp.mkdir_p(rdir)
    is_dir = lsftp.isdir(rdir)
    lsftp.rmdir(rdir)
    lsftp.rmdir(rdir2)
    lsftp.mkdir_p(rdir)     # try partially existing path
    is_dir_partial = lsftp.isdir(rdir)
    lsftp.rmdir(rdir)
    lsftp.rmdir(rdir2)
    lsftp.rmdir('foo')
    assert is_dir
    assert is_dir_partial


# def test_lexists_symbolic(psftp):
#     '''test .lexists() vs. symbolic link'''
#     rsym = 'readme.sym'
#     assert psftp.lexists(rsym)


@SKIP_IF_CI
def test_symlink(lsftp):
    '''test symlink creation'''
    rdest = '/home/test/honey-boo-boo'
    with tempfile_containing() as fname:
        lsftp.put(fname)
        lsftp.symlink(fname, rdest)
        rslt = lsftp.lstat(rdest)
        is_link = S_ISLNK(rslt.st_mode)
        lsftp.remove(rdest)
        lsftp.remove(Path(fname).name)
    assert is_link


def test_exists(sftpserver):
    '''test .exists() fuctionality'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            rfile = 'pub/foo2/bar1/bar1.txt'
            rbad = 'pub/foo2/bar1/peek-a-boo.txt'
            assert sftp.exists(rfile)
            assert sftp.exists(rbad) is False
            assert sftp.exists('pub')


@SKIP_IF_CI
def test_lexists(lsftp):
    '''test .lexists() functionality'''
    with tempfile_containing() as fname:
        base_fname = Path(fname).name
        lsftp.put(fname)
        # rfile = '/home/test/readme.txt'
        rbad = '/home/test/peek-a-boo.txt'
        assert lsftp.lexists(fname)
        lsftp.remove(base_fname)
        assert lsftp.lexists(rbad) is False
