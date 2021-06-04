'''test sftpretty module, setup.py and tests'''

from pep8 import StyleGuide


def test_pep8():
    '''pep8 check the source'''
    # list the specific files or directories to check, directories are recursed
    paths = ['sftpretty', 'setup.py', 'tests']
    p8c = StyleGuide()
    report = p8c.check_files(paths=paths)
    report.print_statistics()
    assert report.get_count() == 0
