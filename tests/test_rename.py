'''test sftpretty.rename'''

from common import tempfile_containing
from pathlib import Path


def test_rename(lsftp):
    '''test rename on remote'''
    contents = 'now is the time\nfor all good...'
    with tempfile_containing(contents=contents) as fname:
        base_fname = Path(fname).name
        if base_fname in lsftp.listdir():
            lsftp.remove(base_fname)
        assert base_fname not in lsftp.listdir()
        lsftp.put(fname)
        lsftp.rename(base_fname, 'bob')
        rdirs = lsftp.listdir()
        assert 'bob' in rdirs
        assert base_fname not in rdirs
        lsftp.remove('bob')


# TODO
# def test_rename_ro(psftp):
#     '''test rename on a read-only server'''
#     with pytest.raises(IOError):
#         psftp.rename('readme.txt', 'bob')
