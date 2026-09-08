'''test sftpretty.get_r'''

from common import conn, rmdir, VFS
from pathlib import Path
from sftpretty import Connection, hash, localtree
from tempfile import mkdtemp


def test_get_r(sftpserver):
    '''test the get_r for remotepath is pwd '.' '''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            localpath = Path(mkdtemp()).as_posix()
            remotepath = '.'
            sftp.get_r(remotepath, localpath)

            local_tree = {}
            remote_tree = {}

            remote_cwd = Path(sftp.pwd).joinpath(remotepath).as_posix()

            localtree(local_tree, localpath, remote_cwd)
            sftp.remotetree(remote_tree, remote_cwd, localpath)

            localdirs = sorted([localdir.replace(localpath, remote_cwd)
                                for localdir in local_tree.keys()])
            remotedirs = sorted(remote_tree.keys())

            assert localdirs == remotedirs

            rmdir(localpath)


def test_get_r_pwd(sftpserver):
    '''test the get_r for remotepath is pwd '/pub/foo2' '''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            localpath = Path(mkdtemp()).as_posix()
            remotepath = 'pub/foo2'
            sftp.get_r(remotepath, localpath)

            local_tree = {}
            remote_tree = {}

            remote_cwd = Path(sftp.pwd).joinpath(remotepath).as_posix()

            localtree(local_tree, localpath, remote_cwd)
            sftp.remotetree(remote_tree, remote_cwd, localpath)

            localdirs = sorted([localdir.replace(localpath, remote_cwd)
                                for localdir in local_tree.keys()])
            remotedirs = sorted(remote_tree.keys())

            assert localdirs == remotedirs

            rmdir(localpath)


def test_get_r_pathed(sftpserver):
    '''test the get_r for localpath, starting deeper then pwd '''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            localpath = Path(mkdtemp()).as_posix()
            remotepath = './bar1'
            sftp.chdir('pub/foo2')
            sftp.get_r(remotepath, localpath)

            local_tree = {}
            remote_tree = {}

            remote_cwd = Path(sftp.pwd).joinpath(remotepath).as_posix()

            localtree(local_tree, localpath, remote_cwd)
            sftp.remotetree(remote_tree, remote_cwd, localpath)

            actual = hash(Path(localpath).joinpath('bar1.txt').as_posix())
            expected = ('126f175986225cdaa8c6eccd1ed9296b487cc799a982ff'
                        'db33818806228c9efb8d4ca14c37641097eb367bdd2f4c'
                        'a7916d63893af38da137251520fff41f3cba')

            assert local_tree.keys() == remote_tree.keys()
            assert actual == expected

            rmdir(localpath)


def test_get_r_cdd(sftpserver):
    '''test the get_r for chdir('pub/foo2')'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            localpath = Path(mkdtemp()).as_posix()
            remotepath = '.'
            sftp.chdir('pub/foo2')
            sftp.get_r(remotepath, localpath)

            local_tree = {}
            remote_tree = {}

            remote_cwd = Path(sftp.pwd).joinpath(remotepath).as_posix()

            localtree(local_tree, localpath, remote_cwd)
            sftp.remotetree(remote_tree, remote_cwd, localpath)

            localdirs = sorted([localdir.replace(localpath, remote_cwd)
                                for localdir in local_tree.keys()])
            remotedirs = sorted(remote_tree.keys())

            assert localdirs == remotedirs

            rmdir(localpath)
