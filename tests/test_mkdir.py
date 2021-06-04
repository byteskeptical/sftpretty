'''test sftpretty.mkdir'''

from common import VFS, conn, SKIP_IF_CI
from sftpretty import Connection, st_mode_to_int


@SKIP_IF_CI
def test_mkdir_mode(lsftp):
    '''test mkdir with mode set to 711'''
    dirname = 'test-dir'
    mode = 711
    assert dirname not in lsftp.listdir()
    lsftp.mkdir(dirname, mode=mode)
    attrs = lsftp.stat(dirname)
    lsftp.rmdir(dirname)
    assert st_mode_to_int(attrs.st_mode) == mode


def test_mkdir(sftpserver):
    '''test mkdir'''
    with sftpserver.serve_content(VFS):
        with Connection(**conn(sftpserver)) as sftp:
            dirname = 'test-dir'
            assert dirname not in sftp.listdir()
            sftp.mkdir(dirname)
            assert dirname in sftp.listdir()
            # clean up
            sftp.rmdir(dirname)


# TODO
# def test_mkdir_ro(psftp):
#     '''test mkdir on a read-only server'''
#     dirname = 'test-dir'
#     assert dirname not in psftp.listdir()
#     with pytest.raises(IOError):
#         psftp.mkdir(dirname)
