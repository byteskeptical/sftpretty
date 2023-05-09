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
            sftp.get_r('.', localpath)

            local_tree = {}
            remote_tree = {}

            remote_cwd = sftp.pwd

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
            sftp.get_r('pub/foo2', localpath)

            local_tree = {}
            remote_tree = {}

            remote_cwd = sftp.pwd

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
            sftp.chdir('pub/foo2')
            localpath = Path(mkdtemp()).as_posix()
            sftp.get_r('./bar1', localpath)

            local_tree = {}
            remote_tree = {}

            remote_cwd = sftp.pwd

            localtree(local_tree, localpath, remote_cwd)
            sftp.remotetree(remote_tree, remote_cwd, localpath)

            actual = hash(remote_cwd + '/bar1.txt')
            expected = ('a69f73cca23a9ac5c8b567dc185a756e97c982164fe258'
                        '59e0d1dcc1475c80a615b2123af1f5f94c11e3e9402c3a'
                        'c558f500199d95b6d3e301758586281dcd26')

            assert local_tree.keys() == remote_tree.keys()
            assert actual == expected

            rmdir(localpath)


def test_get_r_cdd(sftpserver):
    '''test the get_r for chdir('pub/foo2')'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            localpath = Path(mkdtemp()).as_posix()
            sftp.chdir('pub/foo2')
            sftp.get_r('.', localpath)

            local_tree = {}
            remote_tree = {}

            remote_cwd = sftp.pwd

            localtree(local_tree, localpath, remote_cwd)
            sftp.remotetree(remote_tree, remote_cwd, localpath)

            localdirs = sorted([localdir.replace(localpath, remote_cwd)
                                for localdir in local_tree.keys()])
            remotedirs = sorted(remote_tree.keys())

            assert localdirs == remotedirs

            rmdir(localpath)
