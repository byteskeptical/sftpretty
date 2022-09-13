from binascii import hexlify
from concurrent.futures import as_completed, ThreadPoolExecutor
from contextlib import contextmanager
from functools import partial
from logging import (basicConfig, getLogger,
                     DEBUG, debug, ERROR, error, INFO, info, WARNING, warning)
from os import environ, utime
from paramiko import (hostkeys, SFTPClient, Transport, util,
                      AuthenticationException, PasswordRequiredException,
                      SSHException, AgentKey, DSSKey, ECDSAKey, Ed25519Key,
                      RSAKey)
from pathlib import Path
from sftpretty.exceptions import (CredentialException, ConnectionException,
                                  HostKeysException)
from sftpretty.helpers import _callback, hash, localtree, retry, st_mode_to_int
from socket import gaierror
from stat import S_ISDIR, S_ISREG
from tempfile import mkstemp
from uuid import uuid4 as uuid


basicConfig(level=INFO)
log = getLogger(__name__)


class CnOpts(object):
    '''additional connection options beyond authentication

    :ivar bool|str log: initial value: False - Log connection details. If set
        to True, creates a temporary file used to capture logs. If set to an
        existing filepath, logs will be appended.
    :ivar bool compression: initial value: False - Enables compression on the
        transport, if set to True.
    :ivar list|None ciphers: initial value: None - Ordered list of allowed
        ciphers to use for connection.
    :ivar list|None digests: initial value: None - Ordered list of preferred
        digests to use for connection in provided order.
    :ivar dict|None disabled_algorithms: initial value: None - Mapping type to
        an iterable of algorithm identifiers, which will be disabled for the
        lifetime of the transport. Keys should match class builtin attribute.
    :ivar list|None kex: initial value: None - Ordered list of preferred
        key exchange algorithms to use for connection.
    :ivar list|None key_types: initial value: None - Ordered list of allowed
        key types to use for connection.
    :ivar paramiko.hostkeys.HostKeys|None hostkeys: HostKeys object used for
        host key verifcation.
    :param filepath|None knownhosts: initial value: None - Location to load
        hostkeys. If None, tries default unix location  ~/.ssh/known_hosts.
    :returns: (obj) CnOpts - Connection options object, used for passing
        extended options to a Connection object.
    :raises HostKeysException:
    '''
    def __init__(self, knownhosts=None):
        self.ciphers = None
        self.compression = False
        self.digests = None
        self.disabled_algorithms = None
        self.hostkeys = hostkeys.HostKeys()
        self.kex = None
        self.key_types = None
        self.log = False
        if knownhosts is None:
            knownhosts = Path('~/.ssh/known_hosts').expanduser().as_posix()
        try:
            self.hostkeys.load(knownhosts)
        except FileNotFoundError:
            # no known_hosts in the default unix location, windows has none
            raise UserWarning((f'No file or host key found in [{knownhosts}]. '
                               'You will need to explicitly load host keys '
                               '(cnopts.hostkeys.load(filename)) or disable '
                               'host key checking (cnopts.hostkeys = None).'))
        else:
            if len(self.hostkeys.items()) == 0:
                raise HostKeysException('No host keys found!')

    def get_hostkey(self, host):
        '''Return the matching known hostkey to be used for verification or
        raise an SSHException
        :param str host:
            The Hostname or IP of the remote machine.
        :raises SSHException:
        '''
        kval = self.hostkeys.lookup(host)
        # None | {key_type: private_key}
        if kval is None:
            raise SSHException(f'No hostkey for host [{host}] found.')

        # Return the private key from the dictionary
        return list(kval.values())[0]


class Connection(object):
    '''Connects and logs into the specified hostname. Arguments that are not
    given are guessed from the environment.

    :param str host: *Required* - Hostname or address of the remote machine.
    :param None|CnOpts cnopts: *Default: None* - Extended connection options
        set as a CnOpts object.
    :param str|None default_path: *Default: None* - Set the default working
        directory upon connection.
    :param str|None password: *Default: None* - Credential for remote machine.
    :param int port: *Default: 22* - SFTP server port of the remote machine.
    :param str|obj|None private_key: *Default: None* - Path to private key
        file(str) or paramiko.AgentKey object
    :param str|None private_key_pass: *Default: None* - Password to use on
        encrypted private_key.
    :param float|None timeout: *Default: None* - Set channel timeout.
    :param str|None username: *Default: None* - User for remote machine.
    :returns: (obj) Connection to the requested host.
    :raises ConnectionException:
    :raises CredentialException:
    :raises SSHException:
    :raises AuthenticationException:
    :raises PasswordRequiredException:
    :raises HostKeysException:
    '''
    def __init__(self, host, cnopts=None, default_path=None, password=None,
                 port=22, private_key=None, private_key_pass=None,
                 timeout=None, username=None):
        self._transport = None
        self._cnopts = cnopts or CnOpts()
        self._default_path = default_path
        self._set_logging()
        self._set_username(username)
        self._timeout = timeout
        # Begin transport
        self._start_transport(host, port)
        self._set_authentication(password, private_key, private_key_pass)

    def _set_authentication(self, password, private_key, private_key_pass):
        '''Authenticate to transport. Prefer private key if given'''
        if private_key is not None:
            # Use path or provided key object
            if isinstance(private_key, str):
                private_key_file = Path(private_key).expanduser().as_posix()
                if Path(private_key_file).is_file():
                    try:
                        with open(private_key_file, 'rb') as key:
                            key_head = key.readline().decode('utf8')
                        if 'DSA' in key_head:
                            key_type = DSSKey
                        elif 'EC' in key_head:
                            key_type = ECDSAKey
                        elif 'OPENSSH' in key_head:
                            key_type = Ed25519Key
                        elif 'RSA' in key_head:
                            key_type = RSAKey
                        else:
                            raise CredentialException(('Unable to identify '
                                                       'key type from file '
                                                       'provided: '
                                                      f'[{private_key_file}]'))
                    except PermissionError as err:
                        raise err
                    finally:
                        try:
                            private_key = key_type.from_private_key_file(
                                private_key_file, password=private_key_pass)
                        except PasswordRequiredException as err:
                            raise CredentialException(('Key is encrypted and '
                                                       'no password was '
                                                       'provided.'))
                        except SSHException as err:
                            raise err
                else:
                    raise CredentialException(('Path provided is not a file '
                                               'or does not exist, please '
                                               'revise and provide a path to '
                                               'a valid private key.'))
            self._transport.auth_publickey(self._username, private_key)
        elif password is not None:
            self._transport.auth_password(self._username, password)
        else:
            raise CredentialException('No password or key specified.')

    def _set_logging(self):
        '''Set logging for connection'''
        if self._cnopts.log:
            if isinstance(self._cnopts.log, bool):
                # Log to a temporary file.
                flo, self._cnopts.log = mkstemp('.txt', 'sftpretty-')
                util.log_to_file(flo)
            else:
                util.log_to_file(self._cnopts.log)
            log.info(f'Logging to file: [{self._cnopts.log}]')

    def _set_username(self, username):
        '''Set the username for the connection. If not passed, then look to
        the environment. Still nothing? Throw exception.'''
        local_username = environ.get('LOGNAME', None)

        if username is not None:
            self._username = username
        elif local_username is not None:
            self._username = local_username
        else:
            raise CredentialException('No username specified.')

    @contextmanager
    def _sftp_channel(self, keepalive=False):
        '''Establish new SFTP channel.'''
        try:
            _channel = SFTPClient.from_transport(self._transport)

            channel = _channel.get_channel()
            channel.set_name(uuid().hex)
            channel.settimeout(self._timeout)

            if self._default_path is not None:
                _channel.chdir(self._default_path)
                log.info(f'Current Working Directory: [{self._default_path}]')

            yield _channel
        except Exception as err:
            raise err
        finally:
            if not keepalive:
                _channel.close()

    def _start_transport(self, host, port):
        '''Start the transport and set connection options if specified.'''
        try:
            self._transport = Transport((host, port))
            self._transport.set_keepalive(60)
            self._transport.set_log_channel(host)
            self._transport.use_compression(self._cnopts.compression)

            # Set allowed ciphers
            if self._cnopts.ciphers is not None:
                ciphers = self._cnopts.ciphers
                self._transport.get_security_options().ciphers = ciphers
            # Set connection digests
            if self._cnopts.digests is not None:
                digests = self._cnopts.digests
                self._transport.get_security_options().digests = digests
            # Set disabled algorithms
            if self._cnopts.disabled_algorithms is not None:
                disabled_algorithms = self._cnopts.disabled_algorithms
                self._transport.disabled_algorithms = disabled_algorithms
            # Set connection kex
            if self._cnopts.kex is not None:
                kex = self._cnopts.kex
                self._transport.get_security_options().kex = kex
            # Set allowed key types
            if self._cnopts.key_types is not None:
                key_types = self._cnopts.key_types
                self._transport.get_security_options().key_types = key_types

            self._transport.start_client(timeout=self._timeout)

            if self._transport.is_active():
                remote_hostkey = self._transport.get_remote_server_key()
                remote_fingerprint = hexlify(remote_hostkey.get_fingerprint())
                log.info((f'[{host}] Host Key:\n\t'
                          f'Name: {remote_hostkey.get_name()}\n\t'
                          f'Fingerprint: {remote_fingerprint}\n\t'
                          f'Size: {remote_hostkey.get_bits():d}'))

                if self._cnopts.hostkeys is not None:
                    user_hostkey = self._cnopts.get_hostkey(host)
                    user_fingerprint = hexlify(user_hostkey.get_fingerprint())
                    log.info(f'Known Fingerprint: {user_fingerprint}')
                    if user_fingerprint != remote_fingerprint:
                        raise HostKeysException((f'{host} key verification: '
                                                 '[FAILED]'))
            else:
                err = self._transport.get_exception()
                if err:
                    self._transport.close()
                    raise err
        except (AttributeError, gaierror, UnicodeError):
            raise ConnectionException(host, port)
        except Exception as err:
            raise err

    def get(self, remotefile, localpath=None, callback=None,
            preserve_mtime=False, exceptions=None, tries=None, backoff=2,
            delay=1, logger=log, silent=False):
        '''Copies a file between the remote host and the local host.

        :param str remotefile: The remote path and filename to retrieve.
        :param str localpath: The local path to save download.
            If None, file is copied to local current working directory.
        :param callable callback: Optional callback function (form: ``func(
            int, int)``) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param bool preserve_mtime: *Default: False* Sync the modification
            time(st_mtime) on the local file to match the time on the remote.
            (st_atime can differ because stat'ing the localfile can/does update
            it's st_atime)
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: Times to try (not retry) before giving up.
        :param int backoff: Default is 2. Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: Default is 1. Initial delay between retries in
            seconds.
        :param logging.Logger logger: Defaults to built in logger object.
            Logger to use. If None, print.
        :param bool silent: Default is False. If set then no logging will
            be attempted.

        :returns: None

        :raises: IOError
        '''
        @retry(exceptions, tries=tries, backoff=backoff, delay=delay,
               logger=logger, silent=silent)
        def _get(self, remotefile, localpath=None, callback=None,
                 preserve_mtime=False):

            if not localpath:
                localpath = Path(remotefile).name

            if not callback:
                callback = partial(_callback, remotefile, logger=logger)

            with self._sftp_channel() as channel:
                if preserve_mtime:
                    remote_attributes = channel.stat(remotefile)

                channel.get(remotefile, localpath=localpath,
                            callback=callback)

            if preserve_mtime:
                utime(localpath, (remote_attributes.st_atime,
                                  remote_attributes.st_mtime))

        _get(self, remotefile, localpath=localpath, callback=callback,
             preserve_mtime=preserve_mtime)

    def get_d(self, remotedir, localdir, callback=None, pattern=None,
              preserve_mtime=False, exceptions=None, tries=None, backoff=2,
              delay=1, logger=log, silent=False):
        '''Get the contents of remotedir and write to locadir. Non-recursive.

        :param str remotedir: The remote directory to copy locally.
        :param str localdir: The local path to save download.
        :param callable callback: Optional callback function (form: ``func(
            int, int``)) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param str pattern: Filter applied to filenames to transfer only subset
            of files in a directory.
        :param bool preserve_mtime: *Default: False* Sync the modification
            time(st_mtime) on the local file to match the time on the remote.
            (st_atime can differ because stat'ing the localfile can/does update
            it's st_atime)
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: Times to try (not retry) before giving up.
        :param int backoff: *Default is 2*. Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default is 1*. Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Defaults to built in logger object*.
            Logger to use. If None, print.
        :param bool silent: *Default is False*. If set then no logging will
            be attempted.

        :returns: None

        :raises: Any exception raised by operations will be passed through.
        '''
        filelist = self.listdir_attr(remotedir)

        if not Path(localdir).is_dir():
            Path(localdir).mkdir(exist_ok=True, parents=True)
            log.info(f'Creating Folder [{localdir}]!')

        if not pattern:
            paths = [
                     (Path(remotedir).joinpath(attribute.filename).as_posix(),
                      Path(localdir).joinpath(attribute.filename).as_posix(),
                      callback, preserve_mtime, exceptions, tries, backoff,
                      delay, logger, silent)
                     for attribute in filelist if S_ISREG(attribute.st_mode)
                    ]
        else:
            paths = [
                     (Path(remotedir).joinpath(attribute.filename).as_posix(),
                      Path(localdir).joinpath(attribute.filename).as_posix(),
                      callback, preserve_mtime, exceptions, tries, backoff,
                      delay, logger, silent)
                     for attribute in filelist if S_ISREG(attribute.st_mode)
                     if f'{pattern}' in attribute.filename
                    ]

        if paths != []:
            with ThreadPoolExecutor(thread_name_prefix=uuid().hex) as pool:
                threads = {
                           pool.submit(self.get, remote, local,
                                       callback=callback,
                                       preserve_mtime=preserve_mtime,
                                       exceptions=exceptions, tries=tries,
                                       backoff=backoff, delay=delay,
                                       logger=logger, silent=silent): remote
                           for remote, local, callback, preserve_mtime,
                           exceptions, tries, backoff, delay, logger, silent in
                           paths
                          }
                for future in as_completed(threads):
                    name = threads[future]
                    try:
                        data = future.result()
                    except Exception as err:
                        logger.error(f'Thread [{name}]: [FAILED]')
                        raise err
                    else:
                        logger.info(f'Thread [{name}]: [COMPLETE]')
                        return data
        else:
            logger.info(f'No files found in directory [{remotedir}]')

    def get_r(self, remotedir, localdir, callback=None, pattern=None,
              preserve_mtime=False, exceptions=None, tries=None, backoff=2,
              delay=1, logger=log, silent=False):
        '''Recursively copy remotedir structure to localdir

        :param str remotedir: The remote directory to recursively copy.
        :param str localdir: The local path to save recursive download.
        :param callable callback: Optional callback function (form: ``func(
            int, int``)) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param str pattern: Filter applied to filenames to transfer only subset
            of files in a directory.
        :param bool preserve_mtime: *Default: False* Sync the modification
            time(st_mtime) on the local file to match the time on the remote.
            (st_atime can differ because stat'ing the localfile can/does update
            it's st_atime)
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: Times to try (not retry) before giving up.
        :param int backoff: *Default is 2*. Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default is 1*. Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Defaults to built in logger object*.
            Logger to use. If None, print.
        :param bool silent: *Default is False*. If set then no logging will
            be attempted.

        :returns: None

        :raises: Any exception raised by operations will be passed through.
        '''
        self.chdir(remotedir)

        directories = {}
        cwd = self._default_path

        directories[cwd] = [(cwd, Path(localdir).joinpath(
                                       cwd.lstrip('/')).as_posix())]

        self.remotetree(directories, cwd, localdir, recurse=True)

        for tld in directories.keys():
            for remote, local in directories[tld]:
                self.get_d(remote, local, callback=callback,
                           pattern=pattern, preserve_mtime=preserve_mtime,
                           exceptions=exceptions, tries=tries, backoff=backoff,
                           delay=delay, logger=logger, silent=silent)

    def getfo(self, remotefile, flo, callback=None, exceptions=None,
              tries=None, backoff=2, delay=1, logger=log, silent=False):
        '''Copy a remote file (remotepath) to a file-like object, flo.

        :param str remotefile: The remote path and filename to retrieve.
        :param flo: Open file like object ready to write.
        :param callable callback: Optional callback function (form: ``func(
            int, int``)) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: Times to try (not retry) before giving up.
        :param int backoff: *Default is 2*. Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default is 1*. Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Defaults to built in logger object*.
            Logger to use. If None, print.
        :param bool silent: *Default is False*. If set then no logging will
            be attempted.

        :returns: (int) The number of bytes written to the opened file object

        :raises: Any exception raised by operations will be passed through.
        '''
        @retry(exceptions, tries=tries, backoff=backoff, delay=delay,
               logger=logger, silent=silent)
        def _getfo(self, remotefile, flo, callback=None):

            if not callback:
                callback = partial(_callback, remotefile, logger=logger)

            with self._sftp_channel() as channel:
                flo_size = channel.getfo(remotefile, flo, callback=callback)

            return flo_size

        return _getfo(self, remotefile, flo, callback=callback)

    def put(self, localfile, remotepath=None, callback=None, confirm=True,
            preserve_mtime=False, exceptions=None, tries=None, backoff=2,
            delay=1, logger=log, silent=False):
        '''Copies a file between the local host and the remote host.

        :param str localfile: The local path and filename to copy remotely.
        :param str remotepath: Remote location to save file, else the remote
            :atttr:`.pwd` and local filename is used.
        :param callable callback: Optional callback function (form: ``func(
            int, int``)) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param bool confirm: Whether to do a stat() on the file afterwards to
            the file size
        :param bool preserve_mtime: *Default: False* Make the modification
            time(st_mtime) on the remote file match the time on the local.
            (st_atime can differ because stat'ing the localfile can/does update
            it's st_atime)
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: Times to try (not retry) before giving up.
        :param int backoff: *Default is 2*. Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default is 1*. Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Defaults to built in logger object*.
            Logger to use. If None, print.
        :param bool silent: *Default is False*. If set then no logging will
            be attempted.

        :returns: (obj) SFTPAttributes containing details about the given file.

        :raises IOError: if remotepath doesn't exist
        :raises OSError: if localfile doesn't exist
        '''
        @retry(exceptions, tries=tries, backoff=backoff, delay=delay,
               logger=logger, silent=silent)
        def _put(self, localfile, remotepath=None, callback=None,
                 confirm=True, preserve_mtime=False):

            if not remotepath:
                remotepath = Path(localfile).name

            if not callback:
                callback = partial(_callback, localfile, logger=logger)

            if preserve_mtime:
                local_attributes = Path(localfile).stat()
                local_times = (local_attributes.st_atime,
                               local_attributes.st_mtime)

            with self._sftp_channel() as channel:
                remote_attributes = channel.put(localfile,
                                                remotepath=remotepath,
                                                callback=callback,
                                                confirm=confirm)

                if preserve_mtime:
                    channel.utime(remotepath, local_times)
                    remote_attributes = channel.stat(remotepath)

            return remote_attributes

        return _put(self, localfile, remotepath=remotepath, callback=callback,
                    confirm=confirm, preserve_mtime=preserve_mtime)

    def put_d(self, localdir, remotedir, callback=None, confirm=True,
              preserve_mtime=False, exceptions=None, tries=None, backoff=2,
              delay=1, logger=log, silent=False):
        '''Copies a local directory's contents to a remotepath

        :param str localdir: The local directory to copy remotely.
        :param str remotedir: The remote location to save directory.
        :param callable callback: Optional callback function (form: ``func(
            int, int``)) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param bool confirm: Whether to do a stat() on the file afterwards to
            confirm the file size.
        :param bool preserve_mtime: *Default: False* Make the modification
            time(st_mtime) on the remote file match the time on the local.
            (st_atime can differ because stat'ing the localfile can/does update
            it's st_atime)
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: Times to try (not retry) before giving up.
        :param int backoff: *Default is 2*. Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default is 1*. Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Defaults to built in logger object*.
            Logger to use. If None, print.
        :param bool silent: *Default is False*. If set then no logging will
            be attempted.

        :returns: None

        :raises IOError: if remotedir doesn't exist
        :raises OSError: if localdir doesn't exist
        '''
        self.mkdir_p(remotedir)

        paths = [
                 (localpath.as_posix(),
                  Path(remotedir).joinpath(
                      localpath.relative_to(
                          Path(localdir).root).as_posix()).as_posix(),
                  callback, confirm, preserve_mtime, exceptions, tries,
                  backoff, delay, logger, silent)
                 for localpath in Path(localdir).iterdir()
                 if localpath.is_file()
                ]

        if paths != []:
            with ThreadPoolExecutor(thread_name_prefix=uuid().hex) as pool:
                threads = {
                           pool.submit(self.put, local, remote,
                                       callback=callback, confirm=confirm,
                                       preserve_mtime=preserve_mtime,
                                       exceptions=exceptions, tries=tries,
                                       backoff=backoff, delay=delay,
                                       logger=logger, silent=silent): local
                           for local, remote, callback, confirm,
                           preserve_mtime, exceptions, tries, backoff, delay,
                           logger, silent in paths
                          }
                for future in as_completed(threads):
                    name = threads[future]
                    try:
                        data = future.result()
                    except Exception as err:
                        logger.error(f'Thread [{name}]: [FAILED]')
                        raise err
                    else:
                        logger.info(f'Thread [{name}]: [COMPLETE]')
                        return data
        else:
            logger.info(f'No files found in directory [{localdir}]')

    def put_r(self, localdir, remotedir, callback=None, confirm=True,
              preserve_mtime=False, exceptions=None, tries=None, backoff=2,
              delay=1, logger=log, silent=False):
        '''Recursively copies a local directory's contents to a remotepath

        :param str localdir: The local directory to copy remotely.
        :param str remotedir: The remote location to save directory.
        :param callable callback: Optional callback function (form: ``func(
            int, int``)) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param bool confirm: Whether to do a stat() on the file afterwards to
            confirm the file size.
        :param bool preserve_mtime: *Default: False* Make the modification
            time(st_mtime) on the remote file match the time on the local.
            (st_atime can differ because stat'ing the localfile can/does update
            it's st_atime)
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: Times to try (not retry) before giving up.
        :param int backoff: *Default is 2*. Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default is 1*. Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Defaults to built in logger object*.
            Logger to use. If None, print.
        :param bool silent: *Default is False*. If set then no logging will
            be attempted.

        :returns: None

        :raises IOError: if remotedir doesn't exist
        :raises OSError: if localdir doesn't exist
        '''
        directories = {}
        directories['root'] = [(localdir,
                                Path(remotedir).joinpath(localdir).as_posix())]

        localtree(directories, localdir, remotedir, recurse=True)

        for tld in directories.keys():
            for local, remote in directories[tld]:
                self.put_d(local, remote, callback=callback, confirm=confirm,
                           preserve_mtime=preserve_mtime,
                           exceptions=exceptions, tries=tries, backoff=backoff,
                           delay=delay, logger=logger, silent=silent)

    def putfo(self, flo, remotepath=None, file_size=0, callback=None,
              confirm=True, exceptions=None, tries=None, backoff=2,
              delay=1, logger=log, silent=False):
        '''Copies the contents of a file like object to remotepath.

        :param flo: File-like object that supports .read()
        :param str remotepath: The remote location to save contents of object.
        :param int file_size: The size of flo, if not given the second param
            passed to the callback function will always be 0.
        :param callable callback: Optional callback function (form: ``func(
            int, int``)) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param bool confirm: Whether to do a stat() on the file afterwards to
            confirm the file size.
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: Times to try (not retry) before giving up.
        :param int backoff: *Default is 2*. Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default is 1*. Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Defaults to built in logger object*.
            Logger to use. If None, print.
        :param bool silent: *Default is False*. If set then no logging will
            be attempted.

        :returns: (obj) SFTPAttributes containing details about the given file.

        :raises: TypeError, if remotepath not specified, any underlying error
        '''
        @retry(exceptions, tries=tries, backoff=backoff, delay=delay,
               logger=logger, silent=silent)
        def _putfo(self, flo, remotepath=None, file_size=0, callback=None,
                   confirm=True):

            if not remotepath:
                remotepath = Path(flo.name).name

            if not callback:
                callback = partial(_callback, flo, logger=logger)

            with self._sftp_channel() as channel:
                flo_attributes = channel.putfo(flo, remotepath=remotepath,
                                               file_size=file_size,
                                               callback=callback,
                                               confirm=confirm)

            return flo_attributes

        return _putfo(self, flo, remotepath=remotepath, file_size=file_size,
                      callback=callback, confirm=confirm)

    def execute(self, command,
                exceptions=None, tries=None, backoff=2, delay=1, logger=log,
                silent=False):
        '''Execute the given commands on a remote machine.  The command is
        executed without regard to the remote :attr:`.pwd`.

        :param str command: Command to execute.
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: Times to try (not retry) before giving up.
        :param int backoff: *Default is 2*. Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default is 1*. Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Defaults to built in logger object*.
            Logger to use. If None, print.
        :param bool silent: *Default is False*. If set then no logging will
            be attempted.

        :returns: (list of str) Results of the command.

        :raises: Any exception raised by command will be passed through.
        '''
        @retry(exceptions, backoff=backoff, delay=delay, logger=logger,
               silent=silent, tries=tries)
        def _execute(self, command):
            channel = self._transport.open_session()
            channel.exec_command(command)

            output = channel.makefile('rb', -1).readlines()

            if output:
                return output
            else:
                return channel.makefile_stderr('rb', -1).readlines()

        _execute(self, command)

    @contextmanager
    def cd(self, remotepath=None):
        '''Context manager that can change to a optionally specified remote
        directory and restores the old pwd on exit.

        :param str|None remotepath: *Default: None* - Remote path to maintain
            as the current working directory.

        :returns: None

        :raises: IOError, if remote path doesn't exist
        '''
        original_path = self.pwd

        try:
            if remotepath is not None:
                self.chdir(remotepath)
            yield
        except Exception as err:
            raise err
        finally:
            self.chdir(original_path)

    def chdir(self, remotepath):
        '''Change the current working directory on the remote

        :param str remotepath: Remote path to set as current working directory.

        :returns: None

        :raises: IOError, if path does not exist
        '''
        with self._sftp_channel() as channel:
            channel.chdir(remotepath)
            self._default_path = channel.normalize('.')

    def chmod(self, remotepath, mode=777):
        '''Set the permission mode of a remotepath, where mode is an octal.

        :param str remotepath: Remote path to modify permission.
        :param int mode: *Default: 777* - Octal mode to apply on path.

        :returns: None

        :raises: IOError, if the file doesn't exist
        '''
        with self._sftp_channel() as channel:
            channel.chmod(remotepath, mode=int(str(mode), 8))

    def chown(self, remotepath, uid=None, gid=None):
        '''Set uid/gid on remotepath, you may specify either or both.

        :param str remotepath: Remote path to modify ownership.
        :param int uid: User id to set as owner of remote path.
        :param int gid: Group id to set on the remote path.

        :returns: None

        :raises: IOError, if user lacks permission or if the file doesn't exist
        '''
        with self._sftp_channel() as channel:
            if uid is None or gid is None:
                if uid is None and gid is None:
                    return
                remote_attributes = channel.stat(remotepath)
                if uid is None:
                    uid = remote_attributes.st_uid
                if gid is None:
                    gid = remote_attributes.st_gid

            channel.chown(remotepath, uid=uid, gid=gid)

    def close(self):
        '''Terminate transport connection and clean up the bits.'''
        try:
            # Close the transport.
            if self._transport and self._transport.is_active():
                self._transport.close()
            self._transport = None
            # Clean up any loggers
            if self._cnopts.log:
                # remove lingering handlers if any
                lgr = getLogger(__name__)
                if lgr:
                    lgr.handlers = []
        except Exception as err:
            raise err

    def exists(self, remotepath):
        '''Test whether a remotepath exists.

        :param str remotepath: Remote location to verify existance of.

        :returns: (bool) True, if remotepath exists, else False.
        '''
        with self._sftp_channel() as channel:
            try:
                channel.stat(remotepath)
            except IOError as err:
                if err.errno == 2:
                    return False
                else:
                    raise err

            return True

    def getcwd(self):
        '''Return the current working directory on the remote.

        :returns: (str) Remote current working directory. None, if not set.
        '''
        with self._sftp_channel() as channel:
            cwd = channel.getcwd()

        return cwd

    def isdir(self, remotepath):
        '''Determine if remotepath is a directory.

        :param str remotepath: Remote location to test.

        :returns: (bool)
        '''
        with self._sftp_channel() as channel:
            try:
                result = S_ISDIR(channel.stat(remotepath).st_mode)
            except IOError:
                # No such directory
                result = False

        return result

    def isfile(self, remotepath):
        '''Determine if remotepath is a file.

        :param str remotepath: Remote location to test.

        :returns: (bool)
        '''
        with self._sftp_channel() as channel:
            try:
                result = S_ISREG(channel.stat(remotepath).st_mode)
            except IOError:
                # No such file
                result = False

        return result

    def lexists(self, remotepath):
        '''Determine whether remotepath exists.

        :param str remotepath: Remote location to test.

        :returns: (bool), True, if lexists, else False
        '''
        with self._sftp_channel() as channel:
            try:
                channel.lstat(remotepath)
            except IOError:
                return False

        return True

    def listdir(self, remotepath='.'):
        '''Return a sorted list of a directory's contents.

        :param str remotepath: Remote location to search.

        :returns: (list of str) Sorted directory content.

        '''
        with self._sftp_channel() as channel:
            directory = sorted(channel.listdir(remotepath))

        return directory

    def listdir_attr(self, remotepath='.'):
        '''Return a non-sorted list of SFTPAttribute objects for the remote
        directory contents. Will not include the special entries '.' and '..'.

        The returned SFTPAttributes objects will each have an additional field:
        longname, which may contain a formatted string of the file's
        attributes, in unix format. The content of this string will depend on
        the SFTP server.

        :param str remotepath: Remote location to search.

        :returns: (list of SFTPAttributes) Sorted directory content as objects.
        '''
        with self._sftp_channel() as channel:
            directory = sorted(channel.listdir_attr(remotepath),
                               key=lambda attribute: attribute.filename)

        return directory

    def lstat(self, remotepath):
        '''Return information about remote location without following symbolic
        links. Otherwise, the same as .stat().

        :param str remotepath: Remote location to stat.

        :returns: (obj) SFTPAttributes object
        '''
        with self._sftp_channel() as channel:
            lstat = channel.lstat(remotepath)

        return lstat

    def mkdir(self, remotedir, mode=777):
        '''Create a directory and set permission mode. On some systems, mode
        is ignored. Where used, the current umask value is first masked out.

        :param str remotedir: Remote location to create.
        :param int mode: *Default: 777* - Octal mode to apply on path.

        :returns: None
        '''
        with self._sftp_channel() as channel:
            channel.mkdir(remotedir, mode=int(str(mode), 8))

    def mkdir_p(self, remotedir, mode=777):
        '''Create a directory and any missing parent locations as needed. Set
        permission mode, if created. Silently complete if remotedir already
        exists.

        :param str remotedir: Remote location to create.
        :param int mode: *Default: 777* - Octal mode to apply on created paths.

        :returns: None

        :raises: OSError
        '''
        try:
            if self.isdir(remotedir):
                pass
            elif self.isfile(remotedir):
                raise OSError(('A file with the same name as the remotedir, '
                              f'[{remotedir}], already exists.'))
            else:
                parent = Path(remotedir).parent.as_posix()
                stem = Path(remotedir).stem
                if parent and not self.isdir(parent):
                    self.mkdir_p(parent, mode=mode)
                if stem:
                    self.mkdir(remotedir, mode=mode)
        except Exception as err:
            raise err

    def normalize(self, remotepath):
        '''Return the fully expanded path of a given location. This can be used
        to resolve symlinks or determine what the server believes to be the
        :attr:`.pwd`, by passing '.' as remotepath.

        :param str remotepath: Remote location to be normalized.

        :return: (str) Normalized path.

        :raises: IOError, if remotepath can't be resolved
        '''
        with self._sftp_channel() as channel:
            expanded_path = channel.normalize(remotepath)

        return expanded_path

    def open(self, remotefile, mode='r', bufsize=-1):
        '''Open a file on the remote server.

        :param str remotefile: Path of the file to open.
        :param str mode: File access mode, defaults to read-only.
        :param int bufsize: *Default: -1* - Buffering in bytes.

        :returns: (obj) SFTPFile, a file-like object handler.

        :raises: IOError, if the file could not be opened.
        '''
        with self._sftp_channel(keepalive=True) as channel:
            flo = channel.open(remotefile, mode=mode, bufsize=bufsize)

        return flo

    def readlink(self, remotelink):
        '''Return the target of a symlink as an absolute path.

        :param str remotelink: Remote location of the symlink.

        :return: (str) Absolute path to target.
        '''
        with self._sftp_channel() as channel:
            link_destination = channel.normalize(channel.readlink(remotelink))

        return link_destination

    def remotetree(self, container, remotedir, localdir, recurse=True):
        '''recursively descend remote directory mapping the tree to a
        dictionary container.

        :param dict container: Hash table to save remote directory tree.
            {remotedir:
                 [(remotedir/sub-directory,
                   localdir/remotedir/sub-directory)],}
        :param str remotedir: Remote location to descend, use '.' to start at
            :attr:`.pwd`.
        :param str localdir: Location used as root of appended remote paths.
        :param bool recurse: *Default: True*. To recurse or not to recurse
            that is the question.

        :returns: None

        :raises: Exception
        '''
        try:
            localdir = Path(localdir).expanduser().as_posix()
            remotedir = self.normalize(remotedir)
            for attribute in self.listdir_attr(remotedir):
                if S_ISDIR(attribute.st_mode):
                    remote = Path(remotedir).joinpath(
                        attribute.filename).as_posix()
                    local = Path(localdir).joinpath(
                        Path(remote).relative_to(
                            Path(remotedir).anchor).as_posix()).as_posix()
                    if remotedir in container.keys():
                        container[remotedir].append((remote, local))
                    else:
                        container[remotedir] = [(remote, local)]
                    if recurse:
                        self.remotetree(container, remote, localdir,
                                        recurse=recurse)
        except Exception as err:
            raise err

    def remove(self, remotefile):
        '''Delete the remote file. May include a path, if no path, then
        :attr:`.pwd` is used. This method only works on files.

        :param str remotefile: Remote file to delete.

        :returns: None

        :raises: IOError
        '''
        with self._sftp_channel() as channel:
            channel.remove(remotefile)

    def rename(self, remotepath, newpath):
        '''Rename a path on the remote host.

        :param str remotepath: Remote path to rename.

        :param str newpath: New name for remote path.

        :returns: None

        :raises: IOError
        '''
        with self._sftp_channel() as channel:
            channel.posix_rename(remotepath, newpath)

    def rmdir(self, remotedir):
        '''Delete remote directory.

        :param str remotedir: Remote directory to delete.

        :returns: None
        '''
        with self._sftp_channel() as channel:
            channel.rmdir(remotedir)

    def stat(self, remotepath):
        '''Return information about remote location.

        :param str remotepath: Remote location to stat.

        :returns: (obj) SFTPAttributes
        '''
        with self._sftp_channel() as channel:
            stat = channel.stat(remotepath)

        return stat

    def symlink(self, remote_src, remote_dest):
        '''Create a symlink for a remote file on the server

        :param str remote_src: path of original file
        :param str remote_dest: path of the created symlink

        :returns: None

        :raises: any underlying error, IOError if remote_dest already exists
        '''
        with self._sftp_channel() as channel:
            channel.symlink(remote_src, remote_dest)

    def truncate(self, remotepath, size):
        '''Change the size of the file specified by path. Used to modify the
        size of the file, just like the truncate method on Python file objects.
        The new file size is confirmed and returned.

        :param str remotepath: remote file path to modify
        :param int|long size: the new file size

        :returns: (int) new size of file

        :raises: IOError, if file does not exist
        '''
        with self._sftp_channel() as channel:
            channel.truncate(remotepath, size)
            size = channel.state(remotepath).st_size

        return size

    @property
    def active_ciphers(self):
        '''Get tuple of currently used local and remote ciphers.

        :returns:
            (tuple of  str) currently used ciphers (local_cipher,
            remote_cipher)
        '''
        return self._transport.local_cipher, self._transport.remote_cipher

    @property
    def active_compression(self):
        '''Get tuple of local and remote compression status.

        :returns: (tuple of str) Compression status.
            (local_compression, remote_compression)
        '''
        local_compression = self._transport.local_compression
        remote_compression = self._transport.remote_compression

        return local_compression, remote_compression

    @property
    def logfile(self):
        '''Return logging setting.

        :returns: (str) logfile or (bool) False
        '''
        return self._cnopts.log

    @property
    def pwd(self):
        '''Return the current working directory.

        :returns: (str) Current working directory.
        '''
        with self._sftp_channel() as channel:
            pwd = channel.normalize('.')

        return pwd

    @property
    def remote_server_key(self):
        '''Return the remote server's key'''
        return self._transport.get_remote_server_key()

    @property
    def security_options(self):
        '''Return the transport security options.

        :returns: (obj) Security preferences for the underlying transport.
            These are tuples of acceptable `.ciphers`, `.digests`, `.key_types`
            and key exchange algorithms `.kex`, listed in order of preference.
        '''
        return self._transport.get_security_options()

    @property
    def sftp_client(self):
        '''Provide access to the underlying SFTPClient object. Client is not
        handled by context manager. Connection is closed with underlying
        transport if not done explicitly.

        :params: None

        :returns: (obj) Active SFTPClient object.
        '''
        with self._sftp_channel(keepalive=True) as channel:
            return channel

    @property
    def timeout(self):
        '''Get or set the underlying socket timeout for pending IO operations.

        :returns: (float|None) Seconds to wait for pending read/write operation
            before raising socket.timeout, or None for no timeout
        '''
        with self._sftp_channel() as channel:
            _channel = channel.get_channel()
            timeout = _channel.gettimeout()

        return timeout

    @timeout.setter
    def timeout(self, val):
        '''Setter for timeout'''
        self._timeout = val

    def __del__(self):
        '''Attempt to garbage collect if not explicitly closed.'''
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        '''GTFO'''
        self.close()
