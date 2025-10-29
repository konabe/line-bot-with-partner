import logging
from typing import Protocol


class Logger(Protocol):
    def debug(self, msg: str) -> None: ...

    def info(self, msg: str) -> None: ...

    def warning(self, msg: str) -> None: ...

    def error(self, msg: str) -> None: ...

    def exception(self, msg: str) -> None: ...


class StdLogger:
    def __init__(self, name: str = __name__):
        # ルートロガーが未設定なら基本設定を行う（重複設定は避ける）
        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s %(levelname)s %(name)s %(message)s",
            )
        self._logger = logging.getLogger(name)
        # ロガー自身のレベルを明示的に設定
        self._logger.setLevel(logging.DEBUG)

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
