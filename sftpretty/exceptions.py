class ConnectionException(Exception):
    '''Exception raised for connection problems

    Attributes:
        message -- explanation of the error
    '''

    def __init__(self, host, port):
        Exception.__init__(self, host, port)
        self.message = f'Could not connect to host:port [{host}:{port}]!'


class CredentialException(Exception):
    '''Exception raised for credential problems

    Attributes:
        message -- explanation of the error
    '''

    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = message


class HostKeysException(Exception):
    '''Exception raised for HostKeys problems'''

    pass
