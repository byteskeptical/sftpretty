'''test sftpretty.remote_server_key'''

from common import conn, VFS
from paramiko.hostkeys import HostKeys
from sftpretty import Connection


def test_remote_server_key(sftpserver):
    '''test .remote_server_key property'''
    with sftpserver.serve_content(VFS):
        _conn = conn(sftpserver)
        _conn['cnopts'].hostkeys = None
        with Connection(**_conn) as sftp:
            rsk = sftp.remote_server_key
            hks = HostKeys()
            hks.add(hostname=sftpserver.host,
                    keytype=rsk.get_name(),
                    key=rsk)
            hks.save('sftpserver.pub')
