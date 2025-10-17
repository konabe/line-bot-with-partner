from typing import Protocol, Any
import logging


class Logger(Protocol):
    def debug(self, msg: str) -> None: ...
    def info(self, msg: str) -> None: ...
    def warning(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...
    def exception(self, msg: str) -> None: ...


class StdLogger:
    def __init__(self, name: str = __name__):
        self._logger = logging.getLogger(name)

    def debug(self, msg: str) -> None:
        self._logger.debug(msg)

    def info(self, msg: str) -> None:
        self._logger.info(msg)

    def warning(self, msg: str) -> None:
        self._logger.warning(msg)

    def error(self, msg: str) -> None:
        self._logger.error(msg)

    def exception(self, msg: str) -> None:
        self._logger.exception(msg)


class NullLogger:
    def debug(self, msg: str) -> None:
        # テストや一時的にログ出力を無効化したい場合のダミー実装です。意図的に何もしません。
        _ = ("debug", msg)
        return None

    def info(self, msg: str) -> None:
        # テストや一時的にログ出力を無効化したい場合のダミー実装です。意図的に何もしません。
        _ = ("info", msg)
        return None

    def warning(self, msg: str) -> None:
        # テストや一時的にログ出力を無効化したい場合のダミー実装です。意図的に何もしません。
        _ = ("warning", msg)
        return None

    def error(self, msg: str) -> None:
        # テストや一時的にログ出力を無効化したい場合のダミー実装です。意図的に何もしません。
        _ = ("error", msg)
        return None

    def exception(self, msg: str) -> None:
        # テストや一時的にログ出力を無効化したい場合のダミー実装です。意図的に何もしません。
        _ = ("exception", msg)
        return None


def create_logger(name: str = __name__, use_null: bool = False) -> Logger:
    return NullLogger() if use_null else StdLogger(name)
