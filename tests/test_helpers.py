'''test sftpretty.helpers'''

import pytest

from hashlib import md5, new, sha1, sha256, sha3_512
from io import BytesIO
from logging import getLogger, INFO
from sftpretty.helpers import _callback, drivepath, hash, st_mode_to_int
from types import SimpleNamespace


@pytest.mark.parametrize('current, total, percent', (
    (1024, 1024, '100.0%'),
    (512, 1024, '50.0%'),
    (1, 3, '33.3%'),
    (0, 1024, '0.0%')),
    ids=('complete', 'half', 'rounded', 'start'))
def test_callback(current, total, percent, capsys):
    '''test progress prints as a percentage of the total'''
    _callback('eels.txt', current, total)
    printed = capsys.readouterr().out

    assert 'eels.txt' in printed
    assert percent in printed
    assert f'{current}:{total}' in printed


def test_callback_logger(caplog):
    '''test progress is logged when a logger is provided'''
    with caplog.at_level(INFO):
        _callback('eels.txt', 512, 1024, logger=getLogger('sftpretty'))

    assert '50.0%' in caplog.text


def test_callback_zero():
    '''test a zero byte total raises'''
    with pytest.raises(ZeroDivisionError):
        _callback('eels.txt', 0, 0)


@pytest.mark.parametrize('path, expected', (
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
    ('\\server\\share\file.txt', '//server/share\file.txt'),
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


@pytest.mark.parametrize('path', (1024, b'C:\\tmp\\test.txt'),
                         ids=('integer', 'bytes'))
def test_drivepath_unsupported(path):
    '''test a non string argument raises'''
    with pytest.raises(TypeError):
        drivepath(path)


@pytest.mark.parametrize('algorithm', (md5(), sha1(), sha256(), sha3_512()),
                         ids=('md5', 'sha1', 'sha256', 'sha3_512'))
def test_hash_algorithm(algorithm, tempfile_containing):
    '''test file and string digest agree with hashlib, per algorithm'''
    content = 'My hovercraft is full of eels.'
    expected = new(algorithm.name, content.encode()).hexdigest()
    localfile = tempfile_containing(contents=content)

    assert hash(localfile, algorithm=algorithm) == expected
    assert hash(content, algorithm=algorithm) == expected


def test_hash_algorithm_nameless():
    '''test an algorithm without a name attribute raises'''
    with pytest.raises(AttributeError):
        hash('some content', algorithm=object())


def test_hash_algorithm_unknown():
    '''test an unsupported digest name raises'''
    with pytest.raises(ValueError):
        hash('some content', algorithm=SimpleNamespace(name='nonesuch'))


@pytest.mark.parametrize('blocksize', (1, 7, 65536),
                         ids=('byte', 'partial', 'default'))
def test_hash_blocksize(blocksize, tempfile_containing):
    '''test chunked reads digest the same as a single read'''
    content = 'My hovercraft is full of eels.'
    expected = sha3_512(content.encode()).hexdigest()
    localfile = tempfile_containing(contents=content)

    assert hash(localfile, blocksize=blocksize) == expected
    assert hash(BytesIO(content.encode()), blocksize=blocksize) == expected


def test_hash_closed(tempfile_containing):
    '''test a closed file object raises'''
    filestream = open(tempfile_containing(contents='some content'), 'rb')
    filestream.close()

    with pytest.raises(ValueError):
        hash(filestream)


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


@pytest.mark.xfail(reason='unsupported types digest as an empty buffer')
def test_hash_unsupported():
    '''test input that is neither a path, string nor file object raises'''
    with pytest.raises(TypeError):
        hash(1024)


@pytest.mark.parametrize('mode,expected', (
    (0o100400, 400), (0o100644, 644), (0o100711, 711),
    (0o40755, 755), (0o40777, 777)),
    ids=('400', '644', '711', '755', '777'))
def test_st_mode_to_int(mode, expected):
    '''test file type bits are trimmed from the mode'''
    assert st_mode_to_int(mode) == expected


@pytest.mark.parametrize('mode,expected', ((0o41777, 777), (0o104755, 755)),
                         ids=('sticky', 'setuid'))
def test_st_mode_to_int_special(mode, expected):
    '''test set user ID, set group ID and sticky bits are dropped'''
    assert st_mode_to_int(mode) == expected


@pytest.mark.parametrize('val', ('0755', None, 7.55),
                         ids=('string', 'none', 'float'))
def test_st_mode_to_int_unsupported(val):
    '''test a non integer mode raises'''
    with pytest.raises(TypeError):
        st_mode_to_int(val)


@pytest.mark.xfail(raises=ValueError, reason='oct(0) renders as 0o0')
def test_st_mode_to_int_zero():
    '''test a mode carrying no permission bits converts to zero'''
    assert st_mode_to_int(0o100000) == 0
