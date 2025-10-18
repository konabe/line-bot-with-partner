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


def create_logger(name: str = __name__) -> Logger:
    return StdLogger(name)
