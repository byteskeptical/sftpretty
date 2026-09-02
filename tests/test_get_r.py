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

            actual = hash(remote_cwd + '/bar1.txt')
            expected = ('d870af1b9d001a0507935ece059c0b6d75782400bdad43f'
                        '8470ca6e992b8a5bef317a9c645ddbdf4cfb0a2340ae632ec'
                        '9b31286f4ea5b68be9b2d89f4dec5de4'
                        )

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
