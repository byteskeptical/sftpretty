from functools import wraps
from hashlib import new, sha3_512
from io import BytesIO, IOBase
from pathlib import Path
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


def hash(filename, algorithm=sha3_512(), blocksize=65536):
    '''hash contents of a file, file like object or string

    :param bytesIO,IObase,str filename:
        path to file, file object, or string to process
    :param hashlib.hash algorithm:
        hash object to use as digest algorithm
    :param int blocksize:
        size of chunk to read in avoiding memory exhaustion

    :returns: hexdigest

    :raises: Exception

    '''
    buffer = new(algorithm.name)
    if isinstance(filename, str):
        try:
            with open(filename, 'rb') as filestream:
                for chunk in iter(lambda: filestream.read(blocksize), b''):
                    buffer.update(chunk)
        except FileNotFoundError:
            buffer.update(bytes(filename.encode('utf-8')))
    elif isinstance(filename, BytesIO):
        for chunk in iter(lambda: filestream.read1(blocksize), b''):
            buffer.update(chunk)
    elif isinstance(filename, IOBase):
        for chunk in iter(lambda: filestream.read(blocksize), b''):
            buffer.update(chunk)

    return algorithm.hexdigest()


def localtree(container, localdir, remotedir, recurse=True):
    '''recursively descend local directory mapping the tree to a
    dictionary container.

    :param dict container: dictionary object to save directory tree
            {localdir:
                 [(localdir/sub-directory,
                   remotedir/localdir/sub-directory)],}
        {localdir: [(content path, remotedir/content path)],}
    :param str localdir:
        root of local directory to descend, use '.' to start at
        :attr:`.pwd`
    :param str remotedir:
        root of remote directory to append localdir too
        path
    :param bool recurse: *Default: True*. To recurse or not to recurse
        that is the question

    :returns: None

    :raises: Exception

    '''
    try:
        localdir = Path(localdir).absolute().expanduser()
        for localpath in localdir.iterdir():
            if localpath.is_dir():
                local = localpath.as_posix()
                remote = Path(remotedir).joinpath(
                    localpath.relative_to(
                        localdir.anchor).as_posix()).as_posix()
                if localdir.as_posix() in container.keys():
                    container[localdir.as_posix()].append((local, remote))
                else:
                    container[localdir.as_posix()] = [(local, remote)]
                container[localdir.as_posix()].sort()
                if recurse:
                    localtree(container, local, remotedir,
                              recurse=recurse)
    except Exception as err:
        raise err


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
    all_exception_types = tuple(set(x if type(x) == type else x.__class__
                                    for x in exceptions))
    exception_types = tuple(x for x in exceptions if type(x) == type)
    exception_instances = tuple(x for x in exceptions if type(x) != type)

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
                                if type(x) == type(e) and
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
