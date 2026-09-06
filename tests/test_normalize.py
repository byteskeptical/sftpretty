'''test sftpretty.normalize'''

from common import conn, SKIP_IF_WIN, VFS, VFS_HOME
from io import BytesIO
from pathlib import Path
from sftpretty import Connection
from sftpretty.helpers import drivepath
from stat import S_ISLNK


def test_normalize(sftpserver):
    '''test the normalize function'''
    pubpath = Path(drivepath(VFS_HOME)).joinpath('pub')
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            makepath = pubpath.parent.joinpath('make.txt').as_posix()
            assert sftp.normalize('make.txt') == makepath
            assert sftp.normalize('.') == pubpath.parent.as_posix()
            assert sftp.normalize('pub') == pubpath.as_posix()
            sftp.chdir('pub')
            assert sftp.normalize('.') == pubpath.as_posix()


@SKIP_IF_WIN  # CreateSymbolicLinkW stats target on creation, returns ENOENT
def test_normalize_dangling_symlink(lsftp, remote_tmpdir):
    '''test normalize against a symlink whose target is missing'''
    missing = Path(remote_tmpdir).joinpath('gone.txt').as_posix()
    rsym = Path(remote_tmpdir).joinpath('dangling.sym').as_posix()
    lsftp.symlink(missing, rsym)

    assert lsftp.lexists(rsym)
    assert lsftp.exists(rsym) is False
    assert lsftp.normalize(rsym) == missing


@SKIP_IF_WIN  # uses lexical _wfullpath instead of realpath, undereferenced
def test_normalize_symlink(lsftp, remote_tmpdir):
    '''test normalize against a symlink'''
    rfile = Path(remote_tmpdir).joinpath('readme.txt').as_posix()
    rsym = Path(remote_tmpdir).joinpath('readme.sym').as_posix()
    lsftp.putfo(BytesIO(b'My hovercraft is full of eels.'), rfile)
    lsftp.symlink(rfile, rsym)

    assert S_ISLNK(lsftp.lstat(rsym).st_mode)
    assert lsftp.normalize(rsym) == lsftp.normalize(rfile)
    assert lsftp.normalize(rsym) != rsym


def test_pwd(sftpserver):
    '''test the pwd property'''
    pubpath = Path(drivepath(VFS_HOME)).joinpath('pub')
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            sftp.chdir('pub/foo2')
            assert sftp.pwd == pubpath.joinpath('foo2').as_posix()
            sftp.chdir('bar1')
            assert sftp.pwd == pubpath.joinpath('foo2/bar1').as_posix()
            sftp.chdir('../../foo1')
            assert sftp.pwd == pubpath.joinpath('foo1').as_posix()
