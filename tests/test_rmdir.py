'''test sftpretty.rmdir'''

from common import SKIP_IF_CI


@SKIP_IF_CI
def test_rmdir(lsftp):
    '''test mkdir'''
    dirname = 'test-rm'
    lsftp.mkdir(dirname)
    assert dirname in lsftp.listdir()
    lsftp.rmdir(dirname)
    assert dirname not in lsftp.listdir()

# TODO
# def test_rmdir_ro(psftp):
#     '''test rmdir against read-only server'''
#     psftp.chdir('/home/test')
#     with pytest.raises(IOError):
#         psftp.rmdir('pub')
