'''test sftpretty.execute'''


# TODO
# def test_execute_simple_ro(psftp):
#     '''test execute simple on a read-only server '''
#     results = [b'This service allows sftp connections only.\n', ]
#     assert psftp.execute('ls') == results


def test_execute_simple(lsftp):
    '''test execute simple'''
    type_check = type(b'')

    results = lsftp.execute('ls')
    # confirm results are an iterable of strings (version dependent)
    for result in results:
        assert isinstance(result, type_check)
