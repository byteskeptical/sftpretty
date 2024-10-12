from concurrent.futures import as_completed, ThreadPoolExecutor
from contextlib import contextmanager
from functools import partial
from logging import (DEBUG, ERROR, FileHandler, Formatter, getLogger, INFO,
                     StreamHandler)
from os import environ, SEEK_END, utime
from paramiko import (Agent, hostkeys, SFTPClient, SSHConfig, Transport,
                      ConfigParseError, PasswordRequiredException,
                      SSHException, DSSKey, ECDSAKey, Ed25519Key, RSAKey)
from pathlib import Path
from sftpretty.exceptions import (CredentialException, ConnectionException,
                                  HostKeysException, LoggingException)
from sftpretty.helpers import _callback, drivedrop, hash, localtree, retry
from socket import gaierror
from stat import S_ISDIR, S_ISREG
from tempfile import mkstemp
from uuid import uuid4


class CnOpts(object):
    '''Additional connection options beyond authentication.

    :ivar tuple ciphers: *Default: paramiko.Transport.SecurityOptions.ciphers*
         - Ordered list of preferred ciphers for connection.
    :ivar bool compress: *Default: paramiko.Transport.use_compression* -
        Enable or disable compression.
    :ivar tuple compression:
         *Default: paramiko.Transport.SecurityOptions.compression* -
         Ordered tuple of preferred compression algorithms for connection.
    :ivar paramiko.SSHConfig: SSHConfig object used for parsing and
         preforming host based lookups on OpenSSH-style config directives.
    :ivar tuple digests: *Default: paramiko.Transport.SecurityOptions.digests*
         - Ordered tuple of preferred digests/macs for connection.
    :ivar dict disabled_algorithms: *Default: {}* - Mapping type to an
        iterable of algorithm identifiers, which will be disabled for the
        lifetime of the transport. Keys should match class builtin attribute.
    :ivar paramiko.hostkeys.HostKeys hostkeys: HostKeys object used for
        host key verifcation.
    :ivar tuple kex: *Default: paramiko.Transport.SecurityOptions.kex* -
        Ordered tuple of preferred key exchange algorithms for connection.
    :ivar tuple key_types:
         *Default: paramiko.Transport.SecurityOptions.key_types* -
         Ordered tuple of preferred public key types for connection.
    :param str config: *Default: ~/.ssh/config* - File path to load
        config from.
    :param str knownhosts: *Default: ~/.ssh/known_hosts* - File path to load
        hostkeys from.
    :ivar bool|str log: *Default: False* - Log connection details. If set to
        True, creates a temporary file used to capture logs. If set to an
        existing filepath, logs will be appended.
    :ivar str log_level: *Default: info* - Set logging level for connection.
        Choose between debug, error, or info.

    :returns: (obj) CnOpts - Connection options object, used for passing
        extended options to a Connection object.

    :raises ConfigParseError:
    :raises HostKeysException:
    '''
    def __init__(self, config=None, knownhosts=Path(
                 '~/.ssh/known_hosts').expanduser().as_posix()):
        self.ciphers = ('aes256-gcm@openssh.com', 'aes128-gcm@openssh.com',
                        'aes256-ctr', 'aes192-ctr', 'aes128-ctr', 'aes256-cbc',
                        'aes192-cbc', 'aes128-cbc', '3des-cbc')
        self.compress = False
        self.compression = ('none',)
        self.digests = ('hmac-sha2-512', 'hmac-sha2-256',
                        'hmac-sha2-512-etm@openssh.com',
                        'hmac-sha2-256-etm@openssh.com',
                        'hmac-sha1', 'hmac-md5')
        self.disabled_algorithms = {}
        self.hostkeys = hostkeys.HostKeys()
        self.kex = ('ecdh-sha2-nistp521', 'ecdh-sha2-nistp384',
                    'ecdh-sha2-nistp256', 'diffie-hellman-group16-sha512',
                    'diffie-hellman-group-exchange-sha256',
                    'diffie-hellman-group-exchange-sha1')
        self.key_types = ('ssh-ed25519', 'ecdsa-sha2-nistp521',
                          'ecdsa-sha2-nistp384', 'ecdsa-sha2-nistp256',
                          'rsa-sha2-512', 'rsa-sha2-256', 'ssh-rsa', 'ssh-dss')
        self.log = False
        self.log_level = 'info'
        self.ssh_config = SSHConfig()

        if config is not None:
            _config = Path(config).expanduser().resolve()
            if Path(_config).exists():
                self.ssh_config = self.ssh_config.from_path(_config)
            else:
                try:
                    self.ssh_config = self.ssh_config.from_file(_config)
                except ConfigParseError:
                    self.ssh_config = self.ssh_config.from_text(_config)
        else:
            _config = Path('~/.ssh/config').expanduser().resolve()
            if _config.exists():
                self.ssh_config = self.ssh_config.from_path(_config.as_posix())
            else:
                self.ssh_config = self.ssh_config.from_text('Host *')

        if knownhosts is not None:
            try:
                self.hostkeys.load(Path(knownhosts).resolve().as_posix())
            except FileNotFoundError:
                # no known_hosts in the default unix location
                raise UserWarning(
                    f'No file or host key found in [{knownhosts}]. '
                    'You will need to explicitly load host keys '
                    '(cnopts.hostkeys.load(filename)) or disable host '
                    'key verification (CnOpts(knownhosts=None)).'
                )
            else:
                if len(self.hostkeys.items()) == 0:
                    raise HostKeysException('No host keys found!')
        else:
            self.hostkeys = None

    def get_agentkey(self):
        '''Return the list of keys, if any, available through the local
        SSH agent. If no agent is running or one cannot be contacted, an
        empty tuple will be returned.

        :returns: (tuple of AgentKey objects) or (empty tuple)

        :raises SSHException:
        '''
        agent = Agent()
        keys = agent.get_keys()

        return keys

    def get_config(self, host):
        '''Return config options for a given host-match.

        :param str host: Identifier to lookup using OpenSSH's ssh_config
            man page ruleset. The first value matched will be returned.

        :returns: (obj) SSHConfigDict - A dictionary wrapper/subclass for
            per-host configuration structures.
        '''
        cval = self.ssh_config.lookup(host)
        return cval or {}

    def get_hostkey(self, host):
        '''Return the matching known hostkey to be used for verification or
        raise an SSHException.

        :param str host: The Hostname or IP of the remote machine.

        :returns: (obj) PKey - Public key(s) associated with host or None.

        :raises SSHException:
        '''
        kval = self.hostkeys.lookup(host)
        # None | {key_type: private_key}
        if kval is None:
            raise SSHException(f'No hostkey for host [{host}] found.')

        # Return the public key from the dictionary
        return list(kval.values())[0]


class Connection(object):
    '''Connects and logs into the specified hostname. Arguments that are not
    given are guessed from the environment.

    :param str host: *Required* - Hostname or address of the remote machine.
    :param CnOpts|None cnopts: *Default: None* - Extended connection options
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
    :raises HostKeysException:
    :raises LoggingException:
    :raises PasswordRequiredException:
    :raises SSHException:
    '''
    def __init__(self, host, cnopts=None, default_path=None, password=None,
                 port=22, private_key=None, private_key_pass=None,
                 timeout=None, username=None):
        self._cnopts = cnopts or CnOpts()
        self._config = self._cnopts.get_config(host)
        self._default_path = default_path
        self._set_logging()
        self._timeout = self._config.get('connecttimeout') or timeout
        self._transport = None
        self._start_transport(self._config.get('hostname') or host,
                              self._config.get('port') or port)
        self._set_username(self._config.get('user') or username)
        self._set_authentication(password, private_key, private_key_pass)

    def _set_authentication(self, password, private_key, private_key_pass):
        '''Authenticate transport. Prefer private key over password.'''
        if self._config.get('identityfile'):
            private_key = self._config['identityfile'][0]
        if private_key is not None:
            # Use key path or provided key object
            key_types = {'DSA': DSSKey, 'EC': ECDSAKey, 'OPENSSH': Ed25519Key,
                         'RSA': RSAKey}
            if isinstance(private_key, str):
                key_file = Path(private_key).expanduser().absolute().as_posix()
                try:
                    with open(key_file, 'r', encoding='utf-8') as head:
                        key_id = head.readline()[11:][:-18]
                    log.debug(f'Key ID: [{key_id}]')
                    key = key_types[key_id.strip()]
                except KeyError as err:
                    log.error(('Unable to identify key type from file provided'
                              f': \n[{key_file}]'))
                    raise err
                except PasswordRequiredException as err:
                    log.error(('No password provided for encrypted private '
                               'key encrypted private key.'))
                    raise err
                except PermissionError as err:
                    log.error(('File permission preventing user access to:\n'
                              f'[{key_file}]'))
                    raise err
                except SSHException as err:
                    log.error(('Path provided is an invalid key file, a '
                               'directory or does not exist, please revise '
                               'and provide a path to a valid private key.'))
                    raise err
                finally:
                    private_key = key.from_private_key_file(
                        key_file, password=private_key_pass)
            self._transport.auth_publickey(self._username, private_key)
        elif password is not None:
            self._transport.auth_password(self._username, password)
        else:
            raise CredentialException('No password or private key provided.')

    def _set_logging(self):
        '''Set logging location and level for connection'''
        level_map = {'debug': DEBUG, 'error': ERROR, 'info': INFO}
        level = self._config.get('loglevel') or self._cnopts.log_level
        level = level_map[level.lower().strip('1,2,3')]

        try:
            global log
            log = getLogger('SFTPretty')
            if self._cnopts.log:
                if isinstance(self._cnopts.log, bool):
                    # Log to a temporary file.
                    flo, self._cnopts.log = mkstemp('.txt', 'sftpretty-')
                logfile = FileHandler(self._cnopts.log, encoding='utf8')
                logfile.setLevel = (level)
                logfile_formatter = Formatter(('[%(asctime)s] %(levelname)s - '
                                               '%(message)s'))
                logfile.setFormatter(logfile_formatter)
                log.addHandler(logfile)
            console = StreamHandler()
            console.setLevel(level)
            console_formatter = Formatter(('[%(asctime)s] %(levelname)s - '
                                           '%(message)s'))
            console.setFormatter(console_formatter)
            log.addHandler(console)
            log.setLevel(level)
        except KeyError:
            raise LoggingException(('Log level must set to one of following: '
                                    '[debug, error, info].'))

    def _set_username(self, username):
        '''Set the username for the connection. If not passed, then look to
        the environment. Still nothing? Throw CredentialException.'''
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
        _channel = None

        try:
            _channel = SFTPClient.from_transport(self._transport)

            channel = _channel.get_channel()
            channel_name = uuid4().hex
            channel.set_name(channel_name)
            channel.settimeout(self._timeout)
            log.debug(f'Channel Name: [{channel_name}]')

            if self._default_path is not None:
                _channel.chdir(drivedrop(self._default_path))
                log.info(f'Current Working Directory: [{self._default_path}]')

            yield _channel
        except Exception as err:
            raise err
        finally:
            if _channel and not keepalive:
                _channel.close()

    def _start_transport(self, host, port):
        '''Start the transport and set connection options if specified.'''
        try:
            self._transport = Transport((host, int(port)))

            keepalive = self._config.get('serveraliveinterval') or 60
            self._transport.set_keepalive(int(keepalive))
            self._transport.set_log_channel(host)

            compress = self._config.get('compression') or self._cnopts.compress
            self._transport.use_compression(compress=bool(compress))

            # Set disabled algorithms
            disabled_algorithms = self._cnopts.disabled_algorithms
            self._transport.disabled_algorithms = disabled_algorithms
            log.debug(f'Disabled Algorithms: [{disabled_algorithms}]')

            # Security Options
            # Set allowed ciphers
            ciphers = self._config.get('ciphers') or self._cnopts.ciphers
            _ciphers = self._transport.get_security_options().ciphers
            if not isinstance(ciphers, tuple):
                ciphers = tuple(ciphers.split(','))
            self._transport.get_security_options().ciphers = tuple(
                cipher for cipher in ciphers if cipher in _ciphers)
            log.debug(f'Ciphers: [{ciphers}]')
            # Set compression algorithms
            compression = self._cnopts.compression
            self._transport.get_security_options().compression = compression
            log.debug(f'Compression: [{compression}]')
            # Set connection digests
            digests = self._config.get('macs') or self._cnopts.digests
            _digests = self._transport.get_security_options().digests
            if not isinstance(digests, tuple):
                digests = tuple(digests.split(','))
            self._transport.get_security_options().digests = tuple(
                digest for digest in digests if digest in _digests)
            log.debug(f'MACs: [{digests}]')
            # Set connection kex
            kexs = self._config.get('kexalgorithms') or self._cnopts.kex
            _kex = self._transport.get_security_options().kex
            if not isinstance(kexs, tuple):
                kexs = tuple(kexs.split(','))
            self._transport.get_security_options().kex = tuple(
                kex for kex in kexs if kex in _kex)
            log.debug(f'KEX: [{kexs}]')
            # Set allowed key types
            key_types = self._config.get('pubkeyacceptedalgorithms') or\
                self._cnopts.key_types
            _key_types = self._transport.get_security_options().key_types
            if not isinstance(key_types, tuple):
                key_types = tuple(key_types.split(','))
            self._transport.get_security_options().key_types = tuple(
                key_type for key_type in key_types if key_type in _key_types)
            log.debug(f'Public Key Types: [{key_types}]')

            self._transport.start_client(timeout=self._timeout)

            if self._transport.is_active():
                remote_hostkey = self._transport.get_remote_server_key()
                remote_fingerprint = hash(remote_hostkey)
                log.info((f'[{host}] Host Key: \n\t'
                          f'Name: {remote_hostkey.get_name()}\n\t'
                          f'Fingerprint: {remote_fingerprint}\n\t'
                          f'Size: {remote_hostkey.get_bits():d}'))

                if self._cnopts.hostkeys is not None:
                    user_hostkey = self._cnopts.get_hostkey(host)
                    user_fingerprint = hash(user_hostkey)
                    log.info(f'Known Fingerprint: {user_fingerprint}')
                    if user_fingerprint != remote_fingerprint:
                        raise HostKeysException((f'{host} key verification: '
                                                 '[FAILED]'))
            else:
                err = self._transport.get_exception()
                if err:
                    self.close()
                    raise err
        except (AttributeError, gaierror, UnicodeError):
            raise ConnectionException(host, port)
        except Exception as err:
            raise err

    def get(self, remotefile, localpath=None, callback=None,
            max_concurrent_prefetch_requests=None, prefetch=True,
            preserve_mtime=False, resume=False, exceptions=None, tries=None,
            backoff=2, delay=1, logger=getLogger(__name__), silent=False):
        '''Copies a file between the remote host and the local host.

        :param str remotefile: The remote path and filename to retrieve.
        :param str localpath: The local path to save download.
            If None, file is copied to local current working directory.
        :param callable callback: Optional callback function (form: ``func(
            int, int)``) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param bool preserve_mtime: *Default: False* - Sync the modification
            time(st_mtime) on the local file to match the time on the remote.
            (st_atime can differ because stat'ing the localfile can/does update
            it's st_atime).
        :param int max_concurrent_prefetch_requests: *Default: None* - The
            maximum number of concurrent read requests to prefetch.
        :param bool prefetch: *Default: True* - Controls whether prefetching
            is performed.
        :param bool resume: *Default: False* - Continue a previous transfer
            based on destination path matching.
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: *Default: None* - Times to try (not retry) before
            giving up.
        :param int backoff: *Default: 2* - Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default: 1* - Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Default: Logger(__name__)* -
            Logger to use.
        :param bool silent: *Default: False* - If set then no logging will
            be attempted.

        :returns: None

        :raises: IOError
        '''
        @retry(exceptions, tries=tries, backoff=backoff, delay=delay,
               logger=logger, silent=silent)
        def _get(self, remotefile, localpath=None, callback=None,
                 max_concurrent_prefetch_requests=None, prefetch=True,
                 preserve_mtime=False, resume=False):

            if localpath is None:
                localpath = Path(remotefile).name

            if callback is None:
                callback = partial(_callback, remotefile, logger=logger)

            with self._sftp_channel() as channel:
                if resume:
                    if Path(localpath).is_file():
                        localsize = Path(localpath).stat().st_size
                        log.info((f'Resuming existing download of {localpath} '
                                  f'@ {localsize} bytes'))
                    else:
                        localsize = 0
                    remote_attributes = remotesize = channel.stat(remotefile)
                    log.debug(f'[{remotesize.st_size}]: {remotefile}')
                    if localsize < remotesize.st_size:
                        with open(localpath, 'ab') as localfile:
                            with channel.open(remotefile, 'rb') as remotepath:
                                if localsize > 0:
                                    remotepath.seek(localsize)
                                if prefetch:
                                    remotepath.prefetch(remotesize.st_size,
                                                        max_concurrent_prefetch_requests)  # noqa: E501
                                channel._transfer_with_callback(
                                    callback=callback,
                                    file_size=remotesize.st_size,
                                    reader=remotepath,
                                    writer=localfile)
                else:
                    if preserve_mtime:
                        remote_attributes = channel.stat(remotefile)

                    channel.get(remotefile, localpath=localpath,
                                callback=callback, prefetch=prefetch,
                                max_concurrent_prefetch_requests=max_concurrent_prefetch_requests)  # noqa: E501

            if preserve_mtime:
                utime(localpath, (remote_attributes.st_atime,
                                  remote_attributes.st_mtime))

        _get(self, remotefile, localpath=localpath, callback=callback,
             max_concurrent_prefetch_requests=max_concurrent_prefetch_requests,
             prefetch=prefetch, preserve_mtime=preserve_mtime, resume=resume)

    def get_d(self, remotedir, localdir, callback=None,
              max_concurrent_prefetch_requests=None, pattern=None,
              prefetch=True, preserve_mtime=False, resume=False, workers=None,
              exceptions=None, tries=None, backoff=2, delay=1,
              logger=getLogger(__name__), silent=False):
        '''Get the contents of remotedir and write to locadir. Non-recursive.

        :param str remotedir: The remote directory to copy locally.
        :param str localdir: The local path to save download.
        :param callable callback: Optional callback function (form: ``func(
            int, int``)) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param int max_concurrent_prefetch_requests: *Default: None* - The
            maximum number of concurrent read requests to prefetch.
        :param str pattern: *Default: None* - Filter applied to filenames to
            transfer only subset of files in a directory.
        :param bool prefetch: *Default: True* - Controls whether prefetching
            is performed.
        :param bool preserve_mtime: *Default: False* - Sync the modification
            time(st_mtime) on the local file to match the time on the remote.
            (st_atime can differ because stat'ing the localfile can/does update
            it's st_atime)
        :param bool resume: *Default: False* - Continue a previous transfer
            based on destination path matching.
        :param int workers: *Default: None* - If None, defaults to number of
            processors plus 4. Set to less than or equal to allowed
            concurrent connections on server.
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: *Default: None* - Times to try (not retry) before
            giving up.
        :param int backoff: *Default: 2* - Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default: 1* - Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Default: Logger(__name__)* -
            Logger to use.
        :param bool silent: *Default: False* - If set then no logging will
            be attempted.

        :returns: None

        :raises: Any exception raised by operations will be passed through.
        '''
        filelist = self.listdir_attr(remotedir)

        if not Path(localdir).is_dir():
            Path(localdir).mkdir(exist_ok=True, parents=True)
            logger.info(f'Creating Folder [{localdir}]!')

        if pattern is None:
            paths = [
                (Path(remotedir).joinpath(attribute.filename).as_posix(),
                 Path(localdir).joinpath(attribute.filename).as_posix(),
                 callback, max_concurrent_prefetch_requests, prefetch,
                 preserve_mtime, resume, exceptions, tries, backoff,
                 delay, logger, silent)
                for attribute in filelist if S_ISREG(attribute.st_mode)
            ]
        else:
            paths = [
                (Path(remotedir).joinpath(attribute.filename).as_posix(),
                 Path(localdir).joinpath(attribute.filename).as_posix(),
                 callback, max_concurrent_prefetch_requests, prefetch,
                 preserve_mtime, resume, exceptions, tries, backoff,
                 delay, logger, silent)
                for attribute in filelist if S_ISREG(attribute.st_mode)
                if f'{pattern}' in attribute.filename
            ]

        if paths != []:
            thread_prefix = uuid4().hex
            with ThreadPoolExecutor(max_workers=workers,
                                    thread_name_prefix=thread_prefix) as pool:
                logger.debug(f'Thread Prefix: [{thread_prefix}]')
                threads = {
                           pool.submit(self.get, remote, local,
                                       callback=callback,
                                       max_concurrent_prefetch_requests=max_concurrent_prefetch_requests,  # noqa: E501
                                       prefetch=prefetch, resume=resume,
                                       preserve_mtime=preserve_mtime,
                                       exceptions=exceptions, tries=tries,
                                       backoff=backoff, delay=delay,
                                       logger=logger, silent=silent): remote
                           for remote, local, callback,
                           max_concurrent_prefetch_requests, prefetch,
                           preserve_mtime, resume, exceptions, tries, backoff,
                           delay, logger, silent in paths
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

    def get_r(self, remotedir, localdir, callback=None,
              max_concurrent_prefetch_requests=None, pattern=None,
              prefetch=True, preserve_mtime=False, resume=False, workers=None,
              exceptions=None, tries=None, backoff=2, delay=1,
              logger=getLogger(__name__), silent=False):
        '''Recursively copy remotedir structure to localdir

        :param str remotedir: The remote directory to recursively copy.
        :param str localdir: The local path to save recursive download.
        :param callable callback: Optional callback function (form: ``func(
            int, int``)) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param int max_concurrent_prefetch_requests: *Default: None* - The
            maximum number of concurrent read requests to prefetch.
        :param str pattern: *Default: None* - Filter applied to all filenames
            transfering only the subset of files that match.
        :param bool prefetch: *Default: True* - Controls whether prefetching
            is performed.
        :param bool preserve_mtime: *Default: False* - Sync the modification
            time(st_mtime) on the local file to match the time on the remote.
            (st_atime can differ because stat'ing the localfile can/does update
            it's st_atime)
        :param bool resume: *Default: False* - Continue a previous transfer
            based on destination path matching.
        :param int workers: *Default: None* - If None, defaults to number of
            processors plus 4. Set to less than or equal to allowed
            concurrent connections on server.
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: *Default: None* - Times to try (not retry) before
            giving up.
        :param int backoff: *Default: 2* - Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default: 1* - Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Default: Logger(__name__)* -
            Logger to use.
        :param bool silent: *Default: False* - If set then no logging will
            be attempted.

        :returns: None

        :raises: Any exception raised by operations will be passed through.
        '''
        self.chdir(remotedir)

        lwd = Path(localdir).absolute().as_posix()
        rwd = self._default_path

        tree = {}
        tree[rwd] = [(rwd, lwd)]

        self.remotetree(tree, rwd, lwd, recurse=True)
        log.debug(f'Remote Tree: [{tree}]')

        for roots in tree.keys():
            for remote, local in tree[roots]:
                self.get_d(remote, local, callback=callback,
                           max_concurrent_prefetch_requests=max_concurrent_prefetch_requests,  # noqa: E501
                           pattern=pattern, prefetch=prefetch,
                           preserve_mtime=preserve_mtime, resume=resume,
                           workers=workers, exceptions=exceptions, tries=tries,
                           backoff=backoff, delay=delay, logger=logger,
                           silent=silent)

    def getfo(self, remotefile, flo, callback=None,
              max_concurrent_prefetch_requests=None, prefetch=True,
              exceptions=None, tries=None, backoff=2, delay=1,
              logger=getLogger(__name__), silent=False):
        '''Copy a remote file (remotepath) to a file-like object, flo.

        :param str remotefile: The remote path and filename to retrieve.
        :param flo: Open file like object ready to write.
        :param callable callback: Optional callback function (form: ``func(
            int, int``)) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param int max_concurrent_prefetch_requests: *Default: None* - The
            maximum number of concurrent read requests to prefetch.
        :param bool prefetch: *Default: True* - Controls whether prefetching
            is performed.
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: *Default: None* - Times to try (not retry) before
            giving up.
        :param int backoff: *Default: 2* - Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default: 1* - Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Default: Logger(__name__)* -
            Logger to use.
        :param bool silent: *Default: False* - If set then no logging will
            be attempted.

        :returns: (int) The number of bytes written to the opened file object

        :raises: Any exception raised by operations will be passed through.
        '''
        @retry(exceptions, tries=tries, backoff=backoff, delay=delay,
               logger=logger, silent=silent)
        def _getfo(self, remotefile, flo, callback=None,
                   max_concurrent_prefetch_requests=None, prefetch=True):

            if callback is None:
                callback = partial(_callback, remotefile, logger=logger)

            with self._sftp_channel() as channel:
                flo_size = channel.getfo(remotefile, flo, callback=callback,
                                         max_concurrent_prefetch_requests=max_concurrent_prefetch_requests,  # noqa: E501
                                         prefetch=prefetch)

            return flo_size

        return _getfo(self, remotefile, flo, callback=callback,
                      max_concurrent_prefetch_requests=max_concurrent_prefetch_requests,  # noqa: E501
                      prefetch=prefetch)

    def put(self, localfile, remotepath=None, callback=None, confirm=True,
            preserve_mtime=False, resume=False, exceptions=None, tries=None,
            backoff=2, delay=1, logger=getLogger(__name__), silent=False):
        '''Copies a file between the local host and the remote host.

        :param str localfile: The local path and filename to copy remotely.
        :param str remotepath: Remote location to save file, else the remote
            :attr:`.pwd` and local filename is used.
        :param callable callback: Optional callback function (form: ``func(
            int, int``)) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param bool confirm: *Default: True* - Whether to do a stat() on the
            file afterwards to the file size.
        :param bool preserve_mtime: *Default: False* - Make the modification
            time(st_mtime) on the remote file match the time on the local.
            (st_atime can differ because stat'ing the localfile can/does update
            it's st_atime)
        :param bool resume: *Default: False* - Continue a previous transfer
            based on destination path matching.
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: *Default: None* - Times to try (not retry) before
            giving up.
        :param int backoff: *Default: 2* - Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default: 1* - Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Default: Logger(__name__)* -
            Logger to use.
        :param bool silent: *Default: False* - If set then no logging will
            be attempted.

        :returns: (obj) SFTPAttributes containing details about the given file.

        :raises IOError: if remotepath doesn't exist
        :raises OSError: if localfile doesn't exist
        '''
        @retry(exceptions, tries=tries, backoff=backoff, delay=delay,
               logger=logger, silent=silent)
        def _put(self, localfile, remotepath=None, callback=None,
                 confirm=True, preserve_mtime=False, resume=False):

            if remotepath is None:
                remotepath = Path(localfile).name

            if callback is None:
                callback = partial(_callback, localfile, logger=logger)

            if preserve_mtime:
                local_attributes = Path(localfile).stat()
                local_times = (local_attributes.st_atime,
                               local_attributes.st_mtime)

            with self._sftp_channel() as channel:
                remotepath = drivedrop(remotepath)
                if resume:
                    remote = channel.stat(remotepath)
                    if S_ISREG(remote.st_mode):
                        remotesize = remote.st_size
                        log.info((f'Resuming existing upload of {remotepath} '
                                  f'@ {remotesize} bytes'))
                    else:
                        remotesize = 0
                    localsize = Path(localfile).stat().st_size
                    log.debug(f'[{localsize}]: {localfile}')
                    if localsize > remotesize:
                        with channel.open(remotepath, 'ab') as remotefile:
                            remotefile.set_pipelined(True)
                            with open(localfile, 'rb') as localpath:
                                if remotesize > 0:
                                    localpath.seek(remotesize)
                                resumesize = channel._transfer_with_callback(
                                    callback=callback, file_size=localsize,
                                    reader=localpath, writer=remotefile)
                    if confirm:
                        attributes = channel.stat(remotepath)
                        if attributes.st_size != (remotesize + resumesize):
                            raise IOError(('size mismatch in put! '
                                           f'{attributes.st_size} != '
                                           f'{remotesize}'))

                else:
                    attributes = channel.put(localfile, remotepath=remotepath,
                                             callback=callback,
                                             confirm=confirm)

                if preserve_mtime:
                    channel.utime(remotepath, local_times)
                    attributes = channel.stat(remotepath)

            return attributes

        return _put(self, localfile, remotepath=remotepath, callback=callback,
                    confirm=confirm, preserve_mtime=preserve_mtime,
                    resume=resume)

    def put_d(self, localdir, remotedir, callback=None, confirm=True,
              preserve_mtime=False, resume=False, workers=None,
              exceptions=None, tries=None, backoff=2, delay=1,
              logger=getLogger(__name__), silent=False):
        '''Copies a local directory's contents to a remotepath

        :param str localdir: The local directory to copy remotely.
        :param str remotedir: The remote location to save directory.
        :param callable callback: Optional callback function (form: ``func(
            int, int``)) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param bool confirm: *Default: True* - Whether to do a stat() on the
            file afterwards to confirm the file size.
        :param bool preserve_mtime: *Default: False* - Make the modification
            time(st_mtime) on the remote file match the time on the local.
            (st_atime can differ because stat'ing the localfile can/does update
            it's st_atime)
        :param bool resume: *Default: False* - Continue a previous transfer
            based on destination path matching.
        :param int workers: *Default: None* - If None, defaults to number of
            processors plus 4. Set to less than or equal to allowed
            concurrent connections on server.
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: *Default: None* - Times to try (not retry) before
            giving up.
        :param int backoff: *Default: 2* - Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default: 1* - Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Default: Logger(__name__)* -
            Logger to use.
        :param bool silent: *Default: False* - If set then no logging will
            be attempted.

        :returns: None

        :raises IOError: if remotedir doesn't exist
        :raises OSError: if localdir doesn't exist
        '''
        localdir = Path(localdir)

        self.mkdir_p(Path(remotedir).joinpath(localdir.stem).as_posix())

        paths = [
            (localpath.as_posix(),
             Path(remotedir).joinpath(localpath.relative_to(
                 localdir.parent).as_posix()).as_posix(),
             callback, confirm, preserve_mtime, resume, exceptions, tries,
             backoff, delay, logger, silent)
            for localpath in localdir.iterdir()
            if localpath.is_file()
        ]

        if paths != []:
            thread_prefix = uuid4().hex
            with ThreadPoolExecutor(max_workers=workers,
                                    thread_name_prefix=thread_prefix) as pool:
                logger.debug(f'Thread Prefix: [{thread_prefix}]')
                threads = {
                    pool.submit(
                        self.put, local, remote, callback=callback,
                        confirm=confirm, preserve_mtime=preserve_mtime,
                        resume=resume, exceptions=exceptions, tries=tries,
                        backoff=backoff, delay=delay, logger=logger,
                        silent=silent
                    ): local
                    for local, remote, callback, confirm,
                    preserve_mtime, resume, exceptions, tries, backoff,
                    delay, logger, silent in paths
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
              preserve_mtime=False, resume=False, workers=None,
              exceptions=None, tries=None, backoff=2, delay=1,
              logger=getLogger(__name__), silent=False):
        '''Recursively copies a local directory's contents to a remotepath

        :param str localdir: The local directory to copy remotely.
        :param str remotedir: The remote location to save directory.
        :param callable callback: Optional callback function (form: ``func(
            int, int``)) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param bool confirm: *Default: True* - Whether to do a stat() on the
            file afterwards to confirm the file size.
        :param bool preserve_mtime: *Default: False* - Make the modification
            time(st_mtime) on the remote file match the time on the local.
            (st_atime can differ because stat'ing the localfile can/does update
            it's st_atime)
        :param bool resume: *Default: False* - Continue a previous transfer
            based on destination path matching.
        :param int workers: *Default: None* - If None, defaults to number of
            processors plus 4. Set to less than or equal to allowed
            concurrent connections on server.
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: *Default: None* - Times to try (not retry) before
            giving up.
        :param int backoff: *Default: 2* - Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default: 1* - Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Default: Logger(__name__)* -
            Logger to use.
        :param bool silent: *Default: False* - If set then no logging will
            be attempted.

        :returns: None

        :raises IOError: if remotedir doesn't exist
        :raises OSError: if localdir doesn't exist
        '''
        lwd = Path(localdir).absolute().as_posix()
        rwd = self.normalize(remotedir)

        tree = {}
        tree[lwd] = [(lwd, rwd)]

        localtree(tree, lwd, rwd, recurse=True)
        log.debug(f'Local Tree: [{tree}]')

        for roots in tree.keys():
            for local, remote in tree[roots]:
                self.put_d(local, remote, callback=callback, confirm=confirm,
                           preserve_mtime=preserve_mtime, resume=resume,
                           workers=workers, exceptions=exceptions, tries=tries,
                           backoff=backoff, delay=delay, logger=logger,
                           silent=silent)

    def putfo(self, flo, remotepath=None, file_size=None, callback=None,
              confirm=True, exceptions=None, tries=None, backoff=2,
              delay=1, logger=getLogger(__name__), silent=False):
        '''Copies the contents of a file like object to remotepath.

        :param flo: File-like object that supports .read()
        :param str remotepath: The remote location to save contents of object.
        :param int file_size: The size of flo, if not given, calculated
            preventing division by zero in default callback function.
        :param callable callback: Optional callback function (form: ``func(
            int, int``)) that accepts the bytes transferred so far and the
            total bytes to be transferred.
        :param bool confirm: *Default: True* - Whether to do a stat() on the
            file afterwards to confirm the file size.
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: Times to try (not retry) before giving up.
        :param int backoff: *Default: 2* - Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default: 1* - Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Default: Logger(__name__)* -
            Logger to use.
        :param bool silent: *Default: False* - If set then no logging will
            be attempted.

        :returns: (obj) SFTPAttributes containing details about the given file.

        :raises: TypeError, if remotepath not specified, any underlying error
        '''
        @retry(exceptions, tries=tries, backoff=backoff, delay=delay,
               logger=logger, silent=silent)
        def _putfo(self, flo, remotepath=None, file_size=None, callback=None,
                   confirm=True):

            if callback is None:
                callback = partial(_callback, flo, logger=logger)

            if file_size is None:
                file_size = flo.seek(0, SEEK_END)
                flo.seek(0)

            if remotepath is None:
                remotepath = uuid4().hex

            with self._sftp_channel() as channel:
                attributes = channel.putfo(flo, remotepath=remotepath,
                                           file_size=file_size,
                                           callback=callback, confirm=confirm)

            return attributes

        return _putfo(self, flo, remotepath=remotepath, file_size=file_size,
                      callback=callback, confirm=confirm)

    def execute(self, command,
                exceptions=None, tries=None, backoff=2, delay=1,
                logger=getLogger(__name__), silent=False):
        '''Execute the given commands on a remote machine.  The command is
        executed without regard to the remote :attr:`.pwd`.

        :param str command: Command to execute.
        :param Exception exceptions: Exception(s) to check. May be a tuple of
            exceptions to check. IOError or IOError(errno.ECOMM) or (IOError,)
            or (ValueError, IOError(errno.ECOMM))
        :param int tries: *Default: None* - Times to try (not retry) before
            giving up.
        :param int backoff: *Default: 2* - Backoff multiplier. Default will
            double the delay each retry.
        :param int delay: *Default: 1* - Initial delay between retries in
            seconds.
        :param logging.Logger logger: *Default: Logger(__name__)* -
            Logger to use.
        :param bool silent: *Default: False* - If set then no logging will
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

        return _execute(self, command)

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
            channel.chdir(drivedrop(remotepath))
            self._default_path = channel.normalize('.')

    def chmod(self, remotepath, mode=700):
        '''Set the permission mode of a remotepath, where mode is an octal.

        :param str remotepath: Remote path to modify permission.
        :param int mode: *Default: 700* - Octal mode to apply on path.

        :returns: None

        :raises: IOError, if the file doesn't exist
        '''
        with self._sftp_channel() as channel:
            channel.chmod(drivedrop(remotepath), mode=int(str(mode), 8))

    def chown(self, remotepath, uid=None, gid=None):
        '''Set uid/gid on remotepath, you may specify either or both.

        :param str remotepath: Remote path to modify ownership.
        :param int uid: User id to set as owner of remote path.
        :param int gid: Group id to set on the remote path.

        :returns: None

        :raises: IOError, if user lacks permission or if the file doesn't exist
        '''
        with self._sftp_channel() as channel:
            remotepath = drivedrop(remotepath)
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
            if log.hasHandlers():
                # remove lingering handlers if any
                for handle in log.handlers:
                    log.removeHandler(handle)
        except AttributeError:
            pass
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
                channel.lstat(drivedrop(remotepath))
            except IOError:
                return False

        return True

    def listdir(self, remotepath='.'):
        '''Return a sorted list of a directory's contents.

        :param str remotepath: Remote location to search.

        :returns: (list of str) Sorted directory content.

        '''
        with self._sftp_channel() as channel:
            directory = sorted(channel.listdir(drivedrop(remotepath)))

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
            directory = sorted(channel.listdir_attr(drivedrop(remotepath)),
                               key=lambda attribute: attribute.filename)

        return directory

    def lstat(self, remotepath):
        '''Return information about remote location without following symbolic
        links. Otherwise, the same as .stat().

        :param str remotepath: Remote location to stat.

        :returns: (obj) SFTPAttributes object
        '''
        with self._sftp_channel() as channel:
            lstat = channel.lstat(drivedrop(remotepath))

        return lstat

    def mkdir(self, remotedir, mode=700):
        '''Create a directory and set permission mode. On some systems, mode
        is ignored. Where used, the current umask value is first masked out.

        :param str remotedir: Remote location to create.
        :param int mode: *Default: 700* - Octal mode to apply on path.

        :returns: None
        '''
        with self._sftp_channel() as channel:
            channel.mkdir(drivedrop(remotedir), mode=int(str(mode), 8))

    def mkdir_p(self, remotedir, mode=700):
        '''Create a directory and any missing parent locations as needed. Set
        permission mode, if created. Silently complete if remotedir already
        exists.

        :param str remotedir: Remote location to create.
        :param int mode: *Default: 700* - Octal mode to apply on created paths.

        :returns: None

        :raises: OSError
        '''
        try:
            remotedir = drivedrop(remotedir)
            if self.isdir(remotedir):
                return
            elif self.isfile(remotedir):
                raise OSError((f'A file with the same name, [{remotedir}], '
                               'already exists.'))
            else:
                parent = Path(remotedir).parent.as_posix()
                stem = Path(remotedir).stem
                if parent != remotedir:
                    if not self.isdir(parent):
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
            expanded_path = channel.normalize(drivedrop(remotepath))

        return expanded_path

    def open(self, remotefile, bufsize=-1, mode='r'):
        '''Open a file on the remote server.

        :param str remotefile: Path of remote file to open.
        :param str mode: *Default: read-only* - File access mode.
        :param int bufsize: *Default: -1* - Buffering in bytes.

        :returns: (obj) SFTPFile, a file-like object handler.

        :raises: IOError, if the file could not be opened.
        '''
        with self._sftp_channel(keepalive=True) as channel:
            remotefile = drivedrop(remotefile)
            flo = channel.open(remotefile, bufsize=bufsize, mode=mode)

        return flo

    def readlink(self, remotelink):
        '''Return the target of a symlink as an absolute path.

        :param str remotelink: Remote location of the symlink.

        :return: (str) Absolute path to target.
        '''
        with self._sftp_channel() as channel:
            remotelink = drivedrop(remotelink)
            link_destination = channel.normalize(channel.readlink(remotelink))

        return link_destination

    def remotetree(self, container, remotedir, localdir, recurse=True):
        '''Recursively map remote directory tree to a dictionary container.

        :param dict container: Hash table to save remote directory tree.
            {remotedir: [(remotedir/subdir, localdir/remotedir/subdir)]}
        :param str remotedir: Remote location to descend, use '.' to start at
            :attr:`.pwd`.
        :param str localdir: Location used as root of appended remote paths.
        :param bool recurse: *Default: True* - To recurse or not to recurse
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
                        Path(remote).stem).as_posix()
                    if remotedir in container.keys():
                        container[remotedir].append((remote, local))
                    else:
                        container[remotedir] = [(remote, local)]
                    if recurse:
                        self.remotetree(container, remote, local,
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
            channel.remove(drivedrop(remotefile))

    def rename(self, remotepath, newpath):
        '''Rename a path on the remote host.

        :param str remotepath: Remote path to rename.

        :param str newpath: New name for remote path.

        :returns: None

        :raises: IOError
        '''
        with self._sftp_channel() as channel:
            channel.posix_rename(drivedrop(remotepath), drivedrop(newpath))

    def rmdir(self, remotedir):
        '''Delete remote directory.

        :param str remotedir: Remote directory to delete.

        :returns: None
        '''
        with self._sftp_channel() as channel:
            channel.rmdir(drivedrop(remotedir))

    def stat(self, remotepath):
        '''Return information about remote location.

        :param str remotepath: Remote location to stat.

        :returns: (obj) SFTPAttributes
        '''
        with self._sftp_channel() as channel:
            stat = channel.stat(drivedrop(remotepath))

        return stat

    def symlink(self, remote_src, remote_dest):
        '''Create a symlink for a remote file on the server

        :param str remote_src: path of original file
        :param str remote_dest: path of the created symlink

        :returns: None

        :raises: any underlying error, IOError if remote_dest already exists
        '''
        with self._sftp_channel() as channel:
            channel.symlink(remote_src, drivedrop(remote_dest))

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
            remotepath = drivedrop(remotepath)
            channel.truncate(remotepath, size)
            size = channel.stat(remotepath).st_size

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
