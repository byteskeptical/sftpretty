from functools import wraps
from hashlib import sha3_512
from io import BytesIO, IOBase
from stat import S_IMODE
from time import sleep


def _callback(filename, bytes_so_far, bytes_total, logger=None):
    message = ('Transfer of File: [{0}] @ {1:d}/{2:d} bytes '
               '({3:.1f}%)').format(filename, bytes_so_far, bytes_total,
                                    100.0 * bytes_so_far / bytes_total)
    if logger:
        logger.info(message)
    else:
        print(message)


def hash(filename, algorithm=None, blocksize=65536):
    if not algorithm:
        hasher = sha3_512()
    if isinstance(filename, str):
        try:
            with open(filename, 'rb') as filestream:
                buffer = filestream.read(blocksize)
                while len(buffer) > 0:
                    hasher.update(buffer)
                    buffer = filestream.read(blocksize)
        except FileNotFoundError:
            hasher.update(bytes(filename.encode('utf-8')))
    elif isinstance(filename, BytesIO):
        buffer = filename.read1(blocksize)
        while len(buffer) > 0:
            hasher.update(buffer)
            buffer = filename.read1(blocksize)
    elif isinstance(filename, IOBase):
        buffer = filename.read(blocksize)
        while len(buffer) > 0:
            hasher.update(buffer)
            buffer = filename.read(blocksize)

    return hasher.hexdigest()


def retry(exceptions, tries=0, delay=3, backoff=2, silent=False, logger=None):
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
                                if isinstance(e, x)) and not any(x
                                    for x in exception_instances
                                        if type(x) == type(e) and
                                            x.args == e.args)):
                        raise
                    msg = ('Retry ({0:d}/{1:d}):\n {2}\n Retrying in {3} '
                           'second(s)...').format(mtries, tries, str(e)
                                                  if str(e) != ''
                                                  else repr(e), mdelay)
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
