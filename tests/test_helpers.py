'''test sftpretty.helpers'''

import pytest

from hashlib import md5, new, sha1, sha256, sha3_512
from io import BytesIO
from sftpretty.helpers import drivepath, hash


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
    ('\\server\share\file.txt', '//server/share\file.txt'),  # noqa: W605
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
    '''test drivepath input variations across supported platforms'''
    assert drivepath(path) == expected
    assert drivepath(expected) == expected


@pytest.mark.parametrize('algorithm', (md5(), sha1(), sha256(), sha3_512()),
                         ids=('md5', 'sha1', 'sha256', 'sha3_512'))
def test_hash_algorithm(algorithm, tempfile_containing):
    '''test file and string digest agree with hashlib, per algorithm'''
    content = 'My hovercraft is full of eels.'
    expected = new(algorithm.name, content.encode()).hexdigest()
    localfile = tempfile_containing(contents=content)

    assert hash(localfile, algorithm=algorithm) == expected
    assert hash(content, algorithm=algorithm) == expected


@pytest.mark.parametrize('blocksize', (1, 7, 65536),
                         ids=('byte', 'partial', 'default'))
def test_hash_blocksize(blocksize, tempfile_containing):
    '''test chunked reads digest the same as a single read'''
    content = 'My hovercraft is full of eels.'
    expected = sha3_512(content.encode()).hexdigest()
    localfile = tempfile_containing(contents=content)

    assert hash(localfile, blocksize=blocksize) == expected
    assert hash(BytesIO(content.encode()), blocksize=blocksize) == expected


@pytest.mark.parametrize('left, right', (
    ('CASE', 'case'),
    ('some content', 'some different content'),
    ('trailing', 'trailing ')))
def test_hash_distinct(left, right):
    '''test distinct payloads never share a digest'''
    empty = sha3_512(b'').hexdigest()

    assert hash(left) != hash(right)
    assert empty not in (hash(left), hash(right))


@pytest.mark.parametrize('form', ('bytesio', 'path', 'string'))
def test_hash_empty(form, tempfile_containing):
    '''test empty input digests to the empty digest, whatever the form'''
    empty = sha3_512(b'').hexdigest()

    if form == 'path':
        assert hash(tempfile_containing(contents='')) == empty
    elif form == 'string':
        assert hash('') == empty
    else:
        assert hash(BytesIO(b'')) == empty


@pytest.mark.parametrize('form', ('path', 'string', 'bytesio', 'fileobject'))
def test_hash_input(form, tempfile_containing):
    '''test input form digests the same bytes alike'''
    content = 'My hovercraft is full of eels.'
    expected = sha3_512(content.encode()).hexdigest()
    localfile = tempfile_containing(contents=content)

    if form == 'path':
        assert hash(localfile) == expected
    elif form == 'string':
        assert hash(content) == expected
    elif form == 'bytesio':
        assert hash(BytesIO(content.encode())) == expected
    else:
        with open(localfile, 'rb') as filestream:
            assert hash(filestream) == expected


def test_hash_repeatable(tempfile_containing):
    '''test repeated calls do not accumulate state'''
    content = 'My hovercraft is full of eels.'
    localfile = tempfile_containing(contents=content)

    assert hash(localfile) == hash(localfile)
    assert hash('some content') == hash('some content')


@pytest.mark.parametrize('unreadable', ('/C:/Users/test/pub/bar1.txt',
                                        'i-do-not-exist.txt',
                                        'some content', 'a' * 512),
                         ids=('drive', 'missing', 'spaces', 'toolong'))
def test_hash_unreadable(unreadable):
    '''test a string that cannot be opened is digested as a string'''
    assert hash(unreadable) == sha3_512(unreadable.encode()).hexdigest()
