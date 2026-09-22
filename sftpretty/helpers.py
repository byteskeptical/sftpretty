from errno import EBADF, ELOOP, ENOENT, ENOTDIR
from functools import wraps
from hashlib import new, sha3_512
from io import BytesIO, IOBase
from os import scandir
from pathlib import Path, PureWindowsPath
from re import sub
from stat import S_IMODE
from time import sleep


def _callback(filename, bytes_so_far, bytes_total, logger=None):
    '''log transfer progress as a percentage of the total

    :param str filename:
        name of the file being transferred
    :param int bytes_so_far:
        bytes transferred so far
    :param int bytes_total:
        total bytes to transfer
    :param logging.Logger logger:
        logger instance to use. If None, print

    :returns: None

    :raises TypeError:
        when bytes_so_far or bytes_total is not an integer
    :raises ZeroDivisionError:
        when bytes_total is zero
    '''
    message = (f'Transfer of File: [{filename}] @ '
               f'{100.0 * bytes_so_far / bytes_total:.1f}% '
               f'{bytes_so_far:d}:{bytes_total:d} bytes ')
    if logger:
        logger.info(message)
    else:
        print(message)


def drivepath(filepath):
    '''Normalize a filepath to POSIX form, retaining any drive letter

    :param str filepath:
        path to file or string to process

    :returns str: normalized POSIX path, empty input is passed through

    :raises TypeError:
        when filepath is not a string
    '''
    if filepath:
        if '\\' in filepath or PureWindowsPath(filepath).drive:
            host = filepath.lstrip('\\/')
            unc = ((filepath[:1] == '\\' or filepath[:2] == '//') and
                   host != '' and host[1:2] != ':')
            utf = filepath.encode('unicode_escape').decode()
            utf = utf.replace('\\\\', '/')
            utf = sub(r'\\([^xuU])', r'/\1', utf)
            filepath = sub('/{2,}', '/',
                           utf.encode('ascii').decode('unicode_escape'))
            winpath = PureWindowsPath(filepath)
            drive = winpath.drive
            filepath = winpath.as_posix()
            if unc:
                filepath = f'/{filepath}'
            elif drive:
                if not winpath.root:
                    filepath = f'{drive}/{filepath[len(drive):]}'
                filepath = f'/{filepath}'
        if filepath.endswith(':'):
            filepath += '/'

    return filepath


def hash(filename, algorithm=sha3_512(), blocksize=65536):
    '''hash contents of a file, file like object or string

    :param BytesIO,IOBase,str filename:
        path to file, file object, or string to process
    :param hashlib.hash algorithm:
        hash object to use as digest algorithm
    :param int blocksize:
        size of chunk to read in avoiding memory exhaustion

    :returns str: hexdigest

    :raises AttributeError:
        when algorithm has no name attribute
    :raises OSError:
        when reading from a file object fails
    :raises ValueError:
        when algorithm.name is not a supported digest or filename is a
        closed file object
    '''
    buffer = new(algorithm.name)
    if isinstance(filename, str):
        try:
            with open(filename, 'rb') as filestream:
                for chunk in iter(lambda: filestream.read(blocksize), b''):
                    buffer.update(chunk)
        except OSError:
            buffer.update(bytes(filename.encode('utf-8')))
    elif isinstance(filename, bytes):
        buffer.update(filename)
    elif isinstance(filename, BytesIO):
        for chunk in iter(lambda: filename.read1(blocksize), b''):
            buffer.update(chunk)
    elif isinstance(filename, IOBase):
        for chunk in iter(lambda: filename.read(blocksize), b''):
            buffer.update(chunk)

    return buffer.hexdigest()


def localtree(container, localdir, remotedir, recurse=True):
    '''descend local directory mapping the tree to a dictionary container.
    Subdirectories are paired with the remote directory they are created
    in, not with their final path. Upstream function is responsible for
    appending the name of the local directory it is handed to remotedir.

    :param dict container:
        dictionary object to save directory tree
            {localdir: [(localdir/sub-directory, remotedir/localdir)],}
            {localdir: [(content path, remote parent of content path)],}
    :param str localdir:
        root of local directory to descend, use '.' to start at
        :attr:`.pwd`
    :param str remotedir:
        root of remote directory localdir is created in
    :param bool recurse:
        *Default: True*. To recurse or not to recurse that is the
        question

    :returns: None

    :raises AttributeError:
        when localdir is not a string
    :raises FileNotFoundError:
        when localdir does not exist
    :raises NotADirectoryError:
        when localdir is not a directory
    :raises PermissionError:
        when a directory in the tree cannot be read
    '''
    if localdir.startswith(':', 1) or localdir.startswith('\\'):
        localdir = Path(PureWindowsPath(localdir).as_posix())
    else:
        localdir = Path(localdir).expanduser().absolute()

    branches = [(localdir.as_posix(),
                 Path(remotedir).joinpath(localdir.name).as_posix())]
    seen = set()

    while branches:
        branch = None
        localroot, remotedir = branches.pop()
        rootstat = None

        with scandir(localroot) as localpaths:
            for localpath in localpaths:
                try:
                    if not localpath.is_dir():
                        continue
                    if localpath.is_symlink():
                        if rootstat is None:
                            rootstat = Path(localroot).stat()
                            seen.add((rootstat.st_dev, rootstat.st_ino))
                        symstat = localpath.stat()
                        softlink = (symstat.st_dev, symstat.st_ino)
                        if softlink in seen:
                            continue
                        seen.add(softlink)
                except OSError as err:
                    if (err.errno in (EBADF, ELOOP, ENOENT, ENOTDIR) or
                            getattr(err, 'winerror', None)
                            in (21, 123, 1921)):
                        continue
                    raise
                if branch is None:
                    branch = container.get(localroot)
                    if branch is None:
                        container[localroot] = branch = []
                local = f'{localroot}/{localpath.name}'
                branch.append((local, remotedir))
                if recurse:
                    branches.append((local, f'{remotedir}/{localpath.name}'))


def retry(exceptions, tries=0, delay=3, backoff=2, silent=False, logger=None):
    '''Exception type based retry decorator for all your problematic functions

    :param Exception exceptions:
        exception(s) to check. May be a tuple of exceptions to check.
        IOError or IOError(errno.ECOMM) or (IOError,) or
        (ValueError, IOError(errno.ECOMM)
    :param int tries:
        number of times to try (not retry) before giving up
    :param int delay:
        initial delay between retries in seconds
    :param int backoff:
        backoff multiplier
    :param bool silent:
        if set then no logging will be attempted.
    :param logging.Logger logger:
        logger instance to use. If None, print

    :returns function:
        decorated function or the function unchanged when tries is None
        or 0

    :raises Exception:
        whatever the decorated function raises, immediately when it is
        not listed in exceptions, otherwise after tries are exhausted
    :raises TypeError:
        when exceptions holds anything that is not an exception type or
        instance raised from the decorated call
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
    '''SFTPAttributes st_mode returns an stat type that shows more than what
    can be set. Trim off those bits and convert to an int representation.
    If you want an object that was `chmod 711` to return a value of 711, use
    this function.

    :param int val:
        the value of an st_mode attr returned by SFTPAttributes

    :returns int: integer representation of octal mode

    :raises TypeError:
        when val is not an integer
    '''
    return int(str(oct(S_IMODE(val)))[-3:])
