import logging
import pytest

from src.infrastructure.logger import create_logger, StdLogger


def test_create_logger_returns_stdlogger():
    logger = create_logger('test.logger')
    assert isinstance(logger, StdLogger)


def test_stdlogger_logs_messages(caplog):
    caplog.set_level(logging.DEBUG)
    logger = create_logger('test.stdlogger')

    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warning message')
    logger.error('error message')

    texts = [rec.getMessage() for rec in caplog.records]
    assert 'debug message' in texts
    assert 'info message' in texts
    assert 'warning message' in texts
    assert 'error message' in texts


def test_stdlogger_exception_logs_traceback(caplog):
    caplog.set_level(logging.ERROR)
    logger = create_logger('test.stdlogger.exception')
    try:
        raise ValueError('boom')
    except Exception:
        logger.exception('exception occurred')

    # ensure the message was logged and includes our text
    messages = '\n'.join(f"{r.message}" for r in caplog.records)
    assert 'exception occurred' in messages