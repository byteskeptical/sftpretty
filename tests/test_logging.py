'''test CnOpts.log, CnOpts.log_level params and temporary log file creation'''

from common import conn, VFS
from logging import getLogger
from pathlib import Path
from sftpretty import CnOpts, Connection


def test_log_cnopts_explicit_false(sftpserver):
    '''test .logfile returns false when CnOpts.log is set to false'''
    copts = conn(sftpserver)
    cnopts = CnOpts(knownhosts='sftpserver.pub')
    copts['cnopts'] = cnopts
    with sftpserver.serve_content(VFS):
        with Connection(**copts) as sftp:
            assert sftp.logfile is False


def test_log_cnopts_log_level(sftpserver):
    '''test log level is passed to application logger'''
    copts = conn(sftpserver)
    cnopts = CnOpts(knownhosts='sftpserver.pub')
    cnopts.log = True
    cnopts.log_level = 'error'
    copts['cnopts'] = cnopts
    with sftpserver.serve_content(VFS):
        with Connection(**copts) as sftp:
            sftp.listdir()
            log = getLogger('SFTPretty')
            assert log.level == 40


def test_log_cnopts_true(sftpserver):
    '''test .logfile returns temp filename when CnOpts.log is set to True'''
    copts = conn(sftpserver)
    cnopts = CnOpts(knownhosts='sftpserver.pub')
    cnopts.log = True
    copts['cnopts'] = cnopts
    with sftpserver.serve_content(VFS):
        with Connection(**copts) as sftp:
            # we are not writing to a file named 'True'
            assert sftp.logfile == cnopts.log
            assert Path(sftp.logfile).exists()


def test_log_cnopts_user_file(sftpserver):
    '''test .logfile returns temp filename when CnOpts.log is set to True'''
    copts = conn(sftpserver)
    cnopts = CnOpts(knownhosts='sftpserver.pub')
    cnopts.log = Path('~/my-logfile1.txt').expanduser().as_posix()
    copts['cnopts'] = cnopts
    with sftpserver.serve_content(VFS):
        with Connection(**copts) as sftp:
            sftp.listdir()
            assert sftp.logfile == cnopts.log
            assert Path(sftp.logfile).exists()
