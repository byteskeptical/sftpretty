'''test sftpretty module'''

from common import conn, LOCAL, VFS
from pathlib import Path
from sftpretty import Connection
from stat import S_ISLNK


def test_sftp_client(lsftp):
    '''test for access to the underlying active sftpclient'''
    with Connection(**LOCAL) as sftp:
        assert 'normalize' in dir(sftp.sftp_client)
        assert 'readlink' in dir(sftp.sftp_client)

    assert 'normalize' in dir(lsftp.sftp_client)
    assert 'readlink' in dir(lsftp.sftp_client)


def test_mkdir_p(lsftp, remote_tmpdir):
    '''test mkdir_p simple, testing 2 things, oh well'''
    rdir = Path(remote_tmpdir).joinpath('foo/bar/baz').as_posix()
    rdir2 = Path(remote_tmpdir).joinpath('foo/bar').as_posix()
    assert lsftp.exists(rdir) is False
    lsftp.mkdir_p(rdir)
    is_dir = lsftp.isdir(rdir)
    lsftp.rmdir(rdir)
    lsftp.rmdir(rdir2)
    lsftp.mkdir_p(rdir)
    is_dir_partial = lsftp.isdir(rdir)

    assert is_dir
    assert is_dir_partial


# def test_lexists_symbolic(lsftp, remote_tmpdir):
#     '''test lexists vs symbolic link'''
#     rsym = Path(remote_tmpdir).joinpath('readme.sym').as_posix()
#     assert lsftp.lexists(rsym)


def test_symlink(lsftp, remote_tmpdir, tempfile_containing):
    '''test symlink creation'''
    rdest = Path(remote_tmpdir).joinpath('honey-boo-boo').as_posix()
    localfile = tempfile_containing()
    rfile = Path(remote_tmpdir).joinpath(Path(localfile).name).as_posix()
    lsftp.put(localfile, rfile)
    lsftp.symlink(rfile, rdest)

    assert S_ISLNK(lsftp.lstat(rdest).st_mode)


def test_exists(sftpserver):
    '''test exists fuctionality'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            rfile = 'pub/foo2/bar1/bar1.txt'
            rbad = 'pub/foo2/bar1/peek-a-boo.txt'
            assert sftp.exists(rfile)
            assert sftp.exists(rbad) is False
            assert sftp.exists('pub')


def test_lexists(lsftp, remote_tmpdir, tempfile_containing):
    '''test lexists functionality'''
    localfile = tempfile_containing()
    rfile = Path(remote_tmpdir).joinpath(Path(localfile).name).as_posix()
    rbad = Path(remote_tmpdir).joinpath('peek-a-boo.txt').as_posix()
    lsftp.put(localfile, rfile)

    assert lsftp.lexists(rfile)
    lsftp.remove(rfile)
    assert lsftp.lexists(rfile) is False
    assert lsftp.lexists(rbad) is False
