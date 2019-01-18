'''test sftpretty.chdir'''

import pytest

from common import conn, VFS
from sftpretty import Connection


def test_chdir_bad_dir(sftpserver):
    '''try to chdir() to a non-existing remote dir'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            with pytest.raises(IOError):
                sftp.chdir('i-dont-exist')
