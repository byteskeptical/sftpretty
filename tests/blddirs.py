'''methods to build a known local directory structure, used in testing'''

from common import STARS8192
from pathlib import Path


DIR_LIST = [('pub', ),
            ('pub', 'foo1'),
            ('pub', 'foo2'),
            ('pub', 'foo2', 'bar1')]
FILE_LIST = [('read.me',),
             ('pub', 'make.txt'),
             ('pub', 'foo1', 'foo1.txt'),
             ('pub', 'foo2', 'foo2.txt'),
             ('pub', 'foo2', 'bar1', 'bar1.txt')]


def build_dir_struct(local_path):
    '''build directory structure'''
    for dparts in DIR_LIST:
        Path(local_path).joinpath(*dparts).mkdir()
    for fparts in FILE_LIST:
        with open(Path(local_path).joinpath(*fparts).as_posix(),
                  'wb') as fhndl:
            try:
                fhndl.write(STARS8192)
            except TypeError:
                fhndl.write(bytes(STARS8192, 'UTF-8'))
