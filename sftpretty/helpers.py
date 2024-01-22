from collections import deque
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from functools import wraps
from hashlib import new, sha3_512
from io import BytesIO, IOBase
from multiprocessing import Manager
from pathlib import Path, PureWindowsPath
from stat import S_IMODE
from time import sleep


def _callback(filename, bytes_so_far, bytes_total, logger=None):
    message = (f'Transfer of File: [{filename}] @ '
               f'{100.0 * bytes_so_far / bytes_total:.1f}% '
               f'{bytes_so_far:d}:{bytes_total:d} bytes ')
    if logger:
        logger.info(message)
    else:
        print(message)


def _localmap(localdir, remotedir):
    '''Sub-directory mapping local directory to iterable.

    :param str localdir:
        root of local directory to descend, use '.' to start at
        :attr:`.pwd`
    :param str remotedir:
        root of remote directory to append localdir

    :returns: tuple: (localdir, _mapping, Exception or None)

    :raises: None

    '''
    _mapping = deque()

    try:
        if localdir.startswith(':', 1) or localdir.startswith('\\'):
            localdir = PureWindowsPath(localdir)
        else:
            localdir = Path(localdir).expanduser().resolve()

        for localpath in Path(localdir).iterdir():
            if localpath.is_dir():
                local = localpath.as_posix()
                remote = Path(remotedir).joinpath(localpath.name).as_posix()
                _mapping.appendleft((local, remote))
    except Exception as err:
        return localdir, [], err

    return localdir, _mapping, None


def drivedrop(filepath):
    '''Shim to standardize filepaths across windows & unix locations'''
    if PureWindowsPath(filepath).drive:
        filepath = Path('/').joinpath(*Path(filepath).parts[1:]).as_posix()

    return filepath


def hash(content, algorithm=sha3_512(), blocksize=65536):
    '''hash contents of a file, file like object or string

    :param bytesIO,IObase,str content:
        path to file, file object, or string to process
    :param hashlib.hash algorithm:
        hash object to use as digest algorithm
    :param int blocksize:
        size of chunk to read in avoiding memory exhaustion

    :returns: hexdigest

    :raises: Exception

    '''
    buffer = new(algorithm.name)
    if isinstance(content, str):
        try:
            with open(content, 'rb') as filestream:
                for chunk in iter(lambda: filestream.read(blocksize), b''):
                    buffer.update(chunk)
        except FileNotFoundError:
            buffer.update(bytes(content.encode('utf-8')))
    elif isinstance(content, BytesIO):
        for chunk in iter(lambda: filestream.read1(blocksize), b''):
            buffer.update(chunk)
    elif isinstance(content, IOBase):
        for chunk in iter(lambda: filestream.read(blocksize), b''):
            buffer.update(chunk)

    return algorithm.hexdigest()


def localtree(localdir, remotedir, recurse=True):
    '''recursively map local directory using sub-directories as keys.

    :param str localdir:
        root of local directory to descend, use '.' to start at
        :attr:`.pwd`
    :param str remotedir:
        root of remote directory to append localdir
    :param bool recurse: *Default: True*. To recurse or not to recurse
        that is the question

    :returns: dict container

    :raises: Exception

    '''
    with Manager() as manager:
        container = manager.dict()
        with ProcessPoolExecutor() as executor:
            _pool = {
                executor.submit(_localmap, localdir, remotedir): localdir
            }

            while _pool:
                done, _ = wait(_pool, return_when=FIRST_COMPLETED)

                for future in done:
                    localdir, _mappings, err = future.result()
                    if err:
                        print(f'Error processing directory {localdir}: {err}')
                        continue

                    container[localdir.as_posix()] = _mappings

                    if recurse:
                        for _local, _remote in _mappings:
                            if _local not in container.keys():
                                future = executor.submit(_localmap, _local,
                                                         _remote, recurse)
                                _pool[future] = _local

                _pool = {
                    _file: localdir
                    for _file, localdir in _pool.items()
                    if _file not in done
                }

        return dict(container)


def retry(exceptions, tries=0, delay=3, backoff=2, silent=False, logger=None):
    '''Exception type based retry decorator for all your problematic functions

    :param Exception exceptions:
        exception(s) to check. May be a tuple of exceptions to check.
        IOError or IOError(errno.ECOMM) or (IOError,) or
        (ValueError, IOError(errno.ECOMM)
    :param int tries:
        number of times to try (not retry) before giving up.
    :param int delay:
        initial delay between retries in seconds.
    :param int backoff:
        backoff multiplier.
    :param bool silent:
        if set then no logging will be attempted.
    :param logging.logger logger:
        logger instance to use. If None, print.

    :returns: wrapped function

    :raises: Exception

    '''
    try:
        len(exceptions)
    except TypeError:
        exceptions = (exceptions,)
    all_exception_types = tuple(set(x if type(x) is type else x.__class__
                                    for x in exceptions))
    exception_types = tuple(x for x in exceptions if type(x) is type)
    exception_instances = tuple(x for x in exceptions if type(x) is not type)

    def wrapper(f):
        if tries in (None, 0):
            message = 'Retry: [DISABLED]'
            if not silent:
                if logger:
                    logger.debug(message)
                else:
                    print(message)

            return f

        @wraps(f)
        def _retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except all_exception_types as e:
                    if (not any(x for x in exception_types
                                if isinstance(e, x)) and
                        not any(x for x in exception_instances
                                if type(x) is type(e) and
                                x.args == e.args)):
                        raise
                    msg = (f'Retry ({mtries:d}/{tries:d}):\n'
                           f'{str(e) if str(e) != "" else repr(e)}\n'
                           f'Retrying in {mdelay} second(s)...')
                    if not silent:
                        if logger:
                            logger.warning(msg)
                        else:
                            print(msg)
                    sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff

            return f(*args, **kwargs)
        return _retry
    return wrapper


def st_mode_to_int(val):
    '''SFTAttributes st_mode returns an stat type that shows more than what
    can be set.  Trim off those bits and convert to an int representation.
    if you want an object that was `chmod 711` to return a value of 711, use
    this function

    :param int val: the value of an st_mode attr returned by SFTPAttributes

    :returns int: integer representation of octal mode

    '''
    return int(str(oct(S_IMODE(val)))[-3:])
