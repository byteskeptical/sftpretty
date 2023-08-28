Getting Started
===============

While in many ways, sftpretty is just a thin wrapper over paramiko's SFTPClient,
there are a number of ways that we make it more productive and easier to
accomplish common, higher-level tasks. The following snippets show where we
add value to this great module. See the :doc:`sftpretty` docs for a complete
listing.


:meth:`sftpretty.Connection`
----------------------------
The Connection object is the base of sftpretty. It supports connections via
username and password.

.. code-block:: python

    import sftpretty

    sftp = sftpretty.Connection('hostname', username='me', password='secret')
    #
    # ... do sftp operations
    #
    sftp.close()    # close your connection to hostname

The Connection object is also context aware so you can use it with a ``with``
statement.

.. code-block:: python

    import sftpretty

    with sftpretty.Connection('hostname', username='me', password='secret') as sftp:
        #
        # ... do sftp operations
        #
    # connection closed automatically at the end of the with-block

Want to use a DSA, ECDSA, ED25519, or RSA key pair, that is simple too.

.. code-block:: python

    import sftpretty

    with sftpretty.Connection('hostname', username='me', private_key='/path/to/keyfile') as sftp:
        #
        # ... do sftp operations
        #

If your key is password protected, just add ``private_key_pass`` to the parameter list.

.. code-block:: python

    import sftpretty

    with sftpretty.Connection('hostname', username='me', private_key='/path/to/keyfile',
                               private_key_pass='keyfile pass') as sftp:
        #
        # ... do sftp operations
        #

How about a ``paramiko.AgentKey``? No problem, just set the private_key equal to it.

.. code-block:: python

    import sftpretty

    with sftpretty.Connection('hostname', username='me', private_key=my_agentkey) as sftp:
        #
        # ... do sftp operations
        #

The connection object allows the use of an IP address for the ``host`` and the
ability to optionally set the ``port``, which defaults to 22, otherwise.


:meth:`sftpretty.CnOpts`
------------------------
You can specify additional connection options using the sftpretty.CnOpts
object. These options are advanced and not applicable to most uses, because of
this they have been segmented from the Connection parameter list and made
available via the CnOpts obj/parameter.

OpenSSH-style config objects are supported. The user's default home location
``~/.ssh/config`` is always checked though not required unless an alternative
path is provided. Credentials still need to be passed whether using a protected
private key or password authentication.

.. code-block:: python

    import sftpretty

    cnopts = sftpretty.CnOpts(config='/etc/ssh/ssh_config')
    with sftpretty.Connection('host_alias', cnopts=cnopts, password='pass'):
        # do stuff here

Config options always take precedence over parameters if both exist. Keep in
mind there will more than likely be a delta between the security option
algorithms your verion of SSH supports and those supported by our underlying
paramiko dependency.

AVAILABLE OPENSSH CONFIG OPTIONS:
 
  * ``Ciphers`` - Replaces the ciphers parameter in the Connection method.
  * ``Compression`` - False **Default** no compression, True enables.
  * ``ConnectTimeout`` - Specifies the timeout (in seconds) used when
    connecting to the server.
  * ``Host`` - Primary lookup key for host block in config. Supports aliases.
  * ``Hostname`` - Actual host/ip to be used in Connection method.
  * ``IdentityFile`` - Location of the private key to use in Connection method.
  * ``KexAlgorithms`` - Replaces the kex parameter in the Connection method.
  * ``LogLevel`` - Replaces the log_level parameter in the Connection method.
  * ``MACS`` - Replaces the digest parameter in the Connection method.
  * ``Port`` - Set the port to use in Connection method.
  * ``PubkeyAcceptedAlgorithms`` - Replaces the key_types parameter in the
    Connection method.
  * ``ServerAliveInterval`` - Sets a timeout interval in seconds. After
    which if no data is received a request for response is sent to server.
  * ``User`` - Replaces the username parameter in the Connection method.

Host Key checking is enabled by default. Loading of ``~/.ssh/known_hosts`` is
always attempted unless an alternative is passed. If you wish to disable host
key checking, **NOT ADVISED**, you will need to modify the default CnOpts and
set the .hostkeys to None.

.. code-block:: python

    import sftpretty

    cnopts = sftpretty.CnOpts()
    cnopts.hostkeys = None
    with sftpretty.Connection('host', username='me', password='pass', cnopts=cnopts):
        # do stuff here

To use a completely different known_hosts file, you can override CnOpts looking
for ``~/.ssh/known_hosts`` by specifying the file when instantiating.

.. code-block:: python

    import sftpretty

    cnopts = sftpretty.CnOpts(knownhosts='path/to/your/knownhosts')
    cnopts.hostkeys = None
    with sftpretty.Connection('host', username='me', password='pass', cnopts=cnopts):
        # do stuff here

If you wish to use ``~/.ssh/known_hosts`` but add additional known host keys
you can merge with update additional known_host format files by using .load
method.

.. code-block:: python

    import sftpretty

    cnopts = sftpretty.CnOpts()
    cnopts.hostkeys.load('path/to/your/extra_knownhosts')
    with sftpretty.Connection('host', username='me', password='pass', cnopts=cnopts):
        # do stuff here

For both the knownhost parameter and the load argument, sftpretty expands user, so
you can use ``~`` tilde notation in your pathing.

AVAILABLE CONNECTION OPTIONS:

  * ``.ciphers`` - Replaces the ciphers parameter in the Connection method.
  * ``.compress`` - False **Default** no compression, True enables
    compression.
  * ``.compression`` - Preferred order of compression methods, if enabled, by
    the above.
  * ``.config`` - SSHConfig object used for parsing and host-based lookups.
  * ``.digests`` - Replaces the digests parameter in the Connection method.
  * ``.disabled_algorithms`` - Algorithm identifiers to disable in the
    Connection method.
  * ``.kex`` - Replaces the kex parameter in the Connection method.
  * ``.key_types`` - Replaces the key types parameter in the Connection method.
  * ``.log`` - False **Default** logs to console, True logs to temporary file,
    String sets custom location.
  * ``.log_level`` - Set logger verbosity to either debug, error, or
    info **Default**.

Here is a common scenario, you have your connection information stored in a
persistence mechanism, like `yamjam <https://yamjam.rtfd.org/>`_ and when you access
it, it is returned in dictionary form. ``{'host':'myhost', username:'me', ...}``
Just send the dict into the connection object like so.

.. code-block:: python

    import sftpretty

    cinfo = {'host':'hostname', 'username':'me', 'password':'secret', 'port':2222}
    with sftpretty.Connection(**cinfo) as sftp:
        #
        # ... do sftp operations
        #


:meth:`sftpretty.Connection.get`
--------------------------------
In addition to the normal paramiko call, you can optionally set the
``preserve_mtime`` parameter to ``True`` and the operation will make sure that
the modification times on the local copy match those on the server.

.. code-block:: python

    # ...
    sftp.get('myfile', preserve_mtime=True)

Now with the ability to resume a previously started download. Based on local
destination path matching.

.. code-block:: python

    # the download continues right where it left off
    sftp.get('myfile', resume=True)


:meth:`sftpretty.Connection.get_d`
----------------------------------
This sftpretty method is an abstraction above :meth:`.get` that allows you to
copy all the files in a remote directory to a local path.

.. code-block:: python

    # copy all files under public to a local path, preserving modification time
    sftp.get_d('public', 'local-backup', preserve_mtime=True)


:meth:`sftpretty.Connection.get_r`
----------------------------------
This sftpretty method is an abstraction that recursively copies files *and*
directories from the remote to a local path.

.. code-block:: python

    # copy all files *and* directories under public to a local path
    sftp.get_r('public', 'local-backup', preserve_mtime=True)


:meth:`sftpretty.Connection.put`
--------------------------------
In addition to the normal paramiko call, you can optionally set the
``preserve_mtime`` parameter to ``True`` and the operation will make sure that
the modification times on the server copy match those on the local.

.. code-block:: python

    # copy myfile, to the current working directory on the server,
    # preserving modification time
    sftp.put('myfile', preserve_mtime=True)

Now with the ability to resume a prematurely ended upload. Based on remote
destination path matching.

.. code-block:: python

    # save a bit and a byte, continue existing upload
    sftp.put('myfile', resume=True)


:meth:`sftpretty.Connection.put_d`
----------------------------------
The opposite of :meth:`.get_d`, put_d allows you to copy the contents of a
local directory to a remote one via SFTP.

.. code-block:: python

    # copy files from images, to remote static/images directory,
    # preserving modification times on files
    sftp.put_d('images', 'static/images', preserve_mtime=True)


:meth:`sftpretty.Connection.put_r`
----------------------------------
This method copies all files *and* directories from a local path to a remote
path.  It creates directories, and happily succeeds even if the target
directories already exist.

.. code-block:: python

    # recursively copy files + directories from local static, to remote static,
    # preserving modification times on directories and files
    sftp.put_r('static', 'static', preserve_mtime=True)


:meth:`sftpretty.Connection.cd`
-------------------------------
This method is a with-context capable version of :meth:`.chdir`. Restoring the
original directory when the ``with`` statement goes out of scope. It can be
called with a remote directory to temporarily change to.

.. code-block:: python

    with sftp.cd('static'):     # now in ./static
        sftp.chdir('here')      # now in ./static/here
        sftp.chdir('there')     # now in ./static/here/there
    # now back to the original current working directory

Or it can be called without a remote directory to just act as a bookmark you
want to return to later.

.. code-block:: python

    with sftp.cd():             # still in .
        sftp.chdir('static')    # now in ./static
        sftp.chdir('here')      # now in ./static/here
    # now back to the original current working directory


:meth:`sftpretty.Connection.chmod`
----------------------------------
:meth:`.chmod` is a wrapper around paramiko's except for the fact it will
takes an integer representation of the octal mode. No leading 0 or 0o
wanted. We know it's suppose to be an octal, but who really remembers that?

This way it is just like a command line ``chmod 644 readme.txt``
::

    user group other
    rwx  rwx   rwx
    421  421   421

    user  - read/write = 4+2 = 6
    group - read       = 4   = 4
    other - read       = 4   = 4

.. code-block:: python

    sftp.chmod('readme.txt', 644)


:meth:`sftpretty.Connection.chown`
----------------------------------
Allows you to specify just, gid, uid or both. If either gid or uid is None
*default*, then sftpretty does a stat to get the current ids and uses that to
fill in the missing parameter because the underlying paramiko method requires
that you explicitly set both.

**NOTE** uid and gid are integers and relative to each system. Just because you
are uid 102 on your local system, a uid of 102 on the remote system most likely
won't be your login. You will need to do some homework to make sure that you
are setting these values as you intended.


:attr:`sftpretty.Connection.pwd`
--------------------------------
Returns the current working directory. It returns the result of
:meth:`.normalize` but makes your code and intention easier to read.
Paramiko has a method, :meth:`.getcwd`, that we expose, but that method
returns ``None`` if :meth:`.chdir` has not been called prior.

.. code-block:: python

    ...
    >>> print(sftp.getcwd())
    None
    >>> sftp.pwd
    u'/home/test'


:meth:`sftpretty.Connection.listdir`
------------------------------------
The difference here is that sftpretty's version returns a sorted list, by
filename, instead of paramiko's arbitrary order.

.. code-block:: python

    ...
    >>> sftp.listdir()
    [u'pub', u'readme.sym', u'readme.txt']


:meth:`sftpretty.Connection.listdir_attr`
-----------------------------------------
The difference here is that sftpretty's version returns a sorted list, by
SFTPAttribute.filename, instead of paramiko's arbitrary order.

.. code-block:: python

    ...
    >>> for attr in sftp.listdir_attr():
    ...     print attr.filename, attr
    ...
    pub        dr-xrwxr-x   1 501      502             5 19 May 23:22 pub
    readme.sym lrwxr-xr-x   1 501      502            10 21 May 23:29 readme.sym
    readme.txt -r--r--r--   1 501      502          8192 26 May 23:32 readme.txt


:meth:`sftpretty.Connection.mkdir`
----------------------------------
Just like :meth:`.chmod`, the mode is an integer representation of the octal
number to use.  Just like the unix cmd, `chmod` you use 744 not 0744 or 0o744.

.. code-block:: python

    ...
    sftp.mkdir('show', mode=644)  # user r/w, group and other read-only


:meth:`sftpretty.Connection.mkdir_p`
-------------------------------------
A common scenario where you need to create all directories in a path as
needed, setting their mode, if created. Mode argument works just like
:meth:`.chmod`, that is an integer representation of the mode you want.

.. code-block:: python

    ...
    sftp.mkdir_p('pub/show/off')  # will make all non-existing directories


:meth:`sftpretty.Connection.isdir`
----------------------------------
A distillation of stat module attributes returning a simple True/False
for directory confirmation.

.. code-block:: python

    ...
    >>> sftp.isdir('pub')
    True


:meth:`sftpretty.Connection.isfile`
-----------------------------------
A distillation of stat module attributes returning a simple True/False
for file confirmation.

.. code-block:: python

    ...
    >>> sftp.isfile('pub')
    False


:meth:`sftpretty.Connection.readlink`
-------------------------------------
The underlying paramiko method can return either an absolute or a relative path.
sftpretty forces this to always be an absolute path by laundering the result with
a :meth:`.normalize` before returning.

.. code-block:: python

    ...
    >>> sftp.readlink('readme.sym')
    u'/home/test/readme.txt'


:meth:`sftpretty.Connection.exists`
-----------------------------------
Returns True if a remote object exists.

.. code-block:: python

    ...
    >>> sftp.exists('readme.txt')   # a file
    True
    >>> sftp.exists('pub')          # a dir
    True


:meth:`sftpretty.Connection.lexists`
------------------------------------
Like :meth:`.exists`, but returns True for a broken symbolic link.


:meth:`sftpretty.Connection.truncate`
-------------------------------------
Like the underlying `.truncate` method, but sftpretty returns the file's new
size after the operation.

.. code-block:: python

    ...
    >>> sftp.truncate('readme.txt', 4096)
    4096


:meth:`sftpretty.Connection.remotetree`
---------------------------------------
A powerful method that can recursively *default* walk a **remote** directory
structure and store the tree as a dictionary in ``{directory: [(subdir,
localdir/subdir),]}`` form. Used in :meth:`.get_r`.

.. code-block:: python

    import sftpretty

    >>> with sftpretty.Connection('hostname', username='me', password='secret') as sftp:
            directories = {}
            sftp.remotetree(directories, '/', '/tmp')
    >>> directories
    {'/': [('/archives', '/tmp/archives'),
           ('/incoming', '/tmp/incoming'),
           ('/outgoing', '/tmp/outgoing')
          ],
     '/incoming': [('/incoming/amrs', '/tmp/incoming/amrs'),
                   ('/incoming/ffopc', '/tmp/incoming/ffopc'),
                   ('/incoming/gpb', '/tmp/incoming/gpb'),
                   ('/incoming/mgmp', '/tmp/incoming/mgmp'),
                   ('/incoming/temp', '/tmp/incoming/temp')
                  ]
    }


:attr:`sftpretty.Connection.sftp_client`
----------------------------------------
Don't like how we have modified a paramiko method? Use this attribute to get
at the original version. Our goal is to augment not supplant paramiko.


:func:`sftpretty.localtree`
---------------------------
Similar to :meth:`sftpretty.Connection.remotetree` except that it walks a
**local** directory structure. It has the same output format and likewise
stores the resulting tree in a dictionary.

.. code-block:: python

    import sftpretty

    >>> directories = {}
    >>> sftpretty.localtree(directories, '/home/user/downloads', '/tmp')
    >>> directories
    {'/home/user/downloads': [('/home/user/downloads/percona', '/tmp/downloads/percona'),
                              ('/home/user/downloads/wallstreet', '/tmp/downloads/wallstreet')
                             ]
    }


:func:`sftpretty.st_mode_to_int`
--------------------------------
Converts an octal mode result back to an integer representation. The information
returned in SFTPAttribute object ``.stat(*fname*).st_mode`` contains extra
things you probably don't care about, in a form that has been converted from
octal to int so you won't recognize it at first. This function clips the extra
bits and hands you the file mode in a way you'll recognize.

.. code-block:: python

    >>> attr = sftp.stat('readme.txt')
    >>> attr.st_mode
    33188
    >>> sftpretty.st_mode_to_int(attr.st_mode)
    644
