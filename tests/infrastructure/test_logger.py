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


def test_stdlogger_with_existing_root_handler_emits_info():
    import logging as _logging

    class _ListHandler(_logging.Handler):
        def __init__(self, level=_logging.INFO):
            super().__init__(level)
            self.records = []

        def emit(self, record):
            self.records.append(record)

    root = _logging.getLogger()
    # 保存して後で復元
    old_handlers = list(root.handlers)
    old_level = root.level
    try:
        # 既存ハンドラがある状況を再現（Gunicorn想定）
        lst = _ListHandler(level=_logging.INFO)
        root.handlers = [lst]
        root.setLevel(_logging.INFO)

        logger = create_logger('test.stdlogger.root')
        logger.info('root-info-visible')
        logger.debug('root-debug-hidden')

        msgs = [r.getMessage() for r in lst.records]
        assert 'root-info-visible' in msgs
        # ルートが INFO のため DEBUG は出力されない
        assert 'root-debug-hidden' not in msgs
    finally:
        # 復元
        root.handlers = old_handlers
        root.setLevel(old_level)
