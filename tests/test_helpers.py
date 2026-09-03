'''test sftpretty.helpers'''

import pytest

from sftpretty.helpers import drivepath


@pytest.mark.parametrize('path,expected', (
    # drive qualified
    ('C:\tmp\test.txt', '/C:/tmp/test.txt'),
    ('C:\\tmp\test.txt', '/C:/tmp/test.txt'),
    ('C:\notes\run.txt', '/C:/notes/run.txt'),
    ('C:\\Users\\nick\\file.txt', '/C:/Users/nick/file.txt'),
    ('C:/tmp/test.txt', '/C:/tmp/test.txt'),
    ('C:\\tmp/mixed\\sep.txt', '/C:/tmp/mixed/sep.txt'),
    ('D:\\data\\x.txt', '/D:/data/x.txt'),
    ('c:\\lower\\case.txt', '/c:/lower/case.txt'),
    # \t \n \r recover, \a \b \f \v ride through as the chars Python made
    ('C:\bin\app.exe', '/C:/\bin\app.exe'),
    # drive relative and drive roots
    ('C:tmp\\test.txt', '/C:/tmp/test.txt'),
    ('C:', '/C:/'), ('C:/', '/C:/'), ('C:\\', '/C:/'),
    ('/C:', '/C:/'), ('/C:/', '/C:/'),
    # leading backslash is UNC, typed pairs arrive collapsed
    ('\\\\server\\share\\file.txt', '//server/share/file.txt'),
    ('\\server\share\file.txt', '//server/share\file.txt'),  # \s survives
    ('\\tmp\test.txt', '//tmp/test.txt'),
    ('//tmp/test.txt', '//tmp/test.txt'),
    ('//server/share//dbl/f.txt', '//server/share/dbl/f.txt'),
    # relative
    ('tmp\\test.txt', 'tmp/test.txt'),
    ('relative/file.txt', 'relative/file.txt'),
    # canonical and posix forms pass through untouched
    ('/C:/Users/x', '/C:/Users/x'),
    ('/cygdrive/c/Users/x', '/cygdrive/c/Users/x'),
    ('/home/user/file.txt', '/home/user/file.txt'),
    ('/home/user/we\tird.txt', '/home/user/we\tird.txt'),
    # data survives the conversion
    ('C:/tmp/café.txt', '/C:/tmp/café.txt'),
    ('C:/tmp/日本語.txt', '/C:/tmp/日本語.txt'),
    ('C:/a//b/c.txt', '/C:/a/b/c.txt'),
    # degenerate
    ('', ''), (None, None)
))
def test_drivepath(path, expected):
    assert drivepath(path) == expected
    assert drivepath(expected) == expected
