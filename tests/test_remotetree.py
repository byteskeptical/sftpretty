'''test sftpretty.remotetree'''

import pytest

from common import conn, VFS
from sftpretty import Connection


def test_remotetree(sftpserver):
    '''test the remotetree function, with recurse'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            directories = {}

            sftp.remotetree(directories,
                            '.',
                            '/tmp')

            dkeys = ['/home/test',
                     '/home/test/pub',
                     '/home/test/pub/foo2']

            dvalues = [[('/home/test/pub', '/tmp/home/test/pub')],
                       [('/home/test/pub/foo1', '/tmp/home/test/pub/foo1'),
                        ('/home/test/pub/foo2', '/tmp/home/test/pub/foo2')],
                       [('/home/test/pub/foo2/bar1',
                         '/tmp/home/test/pub/foo2/bar1')]]

            assert list(directories.keys()) == dkeys
            assert list(directories.values()) == dvalues


def test_remotetree_no_recurse(sftpserver):
    '''test the remotetree function, without recursing'''

    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            directories = {}

            sftp.remotetree(directories,
                            '.',
                            '/tmp',
                            recurse=False)

            dkeys = ['/home/test']
            dvalues = [[('/home/test/pub', '/tmp/home/test/pub')]]

            assert list(directories.keys()) == dkeys
            assert list(directories.values()) == dvalues
