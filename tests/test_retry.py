import pytest

from logging import DEBUG, getLogger, StreamHandler
from retry import retry


class RetryableError(Exception):
    pass


class AnotherRetryableError(Exception):
    pass


class UnexpectedError(Exception):
    pass


def test_no_retry_required():

    @retry(RetryableError, tries=4, delay=0.1)
    def succeeds(counter=0):
        counter += 1
        return 'success'

    r = succeeds()

    assert r == 'success'
    assert counter == 1

def test_retries_once():

    @retry(RetryableError, tries=4, delay=0.1)
    def fails_once(counter=0):
        counter += 1
        if counter < 2:
            raise RetryableError('failed')
        else:
            return 'success'

    r = fails_once()

    assert r == 'success'
    assert counter == 2

def test_limit_is_reached():

    @retry(RetryableError, tries=4, delay=0.1)
    def always_fails(counter=0):
        counter += 1
        raise RetryableError('failed')

    with pytest.raises(RetryableError, match='failed'):
        always_fails()

    assert counter == 4

def test_multiple_exception_types():

    @retry((RetryableError, AnotherRetryableError), tries=4, delay=0.1)
    def raise_multiple_exceptions(counter=0):
        counter += 1
        if counter == 1:
            raise RetryableError('a retryable error')
        elif counter == 2:
            raise AnotherRetryableError('another retryable error')
        else:
            return 'success'

    r = raise_multiple_exceptions()

    assert r == 'success'
    assert counter == 3

def test_unexpected_exception_does_not_retry():

    @retry(RetryableError, tries=4, delay=0.1)
    def raise_unexpected_error():
        raise UnexpectedError('unexpected error')

    with pytest.raises(UnexpectedError, match='unexpected error'):
        raise_unexpected_error()

@pytest.fixture(autouse=True)
def test_using_a_logger(caplog):
    _caplog = caplog
    expected = {'DEBUG': 'success',
                'ERROR': 'failed',
                'WARNING': ('Retry (4/4):\nfailed\nRetrying in 0.1 '
                            'second(s)...')}
    records = {}

    sh = StreamHandler()
    log = getLogger(__name__)
    log.addHandler(sh)

    @retry(RetryableError, tries=4, delay=0.1, logger=log)
    def fails_once(counter=0):
        counter += 1
        if counter < 2:
            log.error('failed')
            raise RetryableError('failed')
        else:
            log.debug('success')
            for record in _caplog.records:
                records[record.levelname] = record.message
            return 'success'

    with _caplog.at_level(DEBUG):
        r = fails_once()

    assert r == 'success'
    assert counter == 2
    assert expected == records
