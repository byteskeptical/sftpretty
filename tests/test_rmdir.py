'''test sftpretty.rmdir'''


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
#     psftp.chdir(Path.home().as_posix())
#     with pytest.raises(IOError):
#         psftp.rmdir('pub')
