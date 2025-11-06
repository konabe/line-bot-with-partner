import os

from dotenv import load_dotenv
from flask import Flask
from linebot.v3.webhook import WebhookHandler

from .application.bind_routes import bind_routes
from .application.usecases.send_startup_notification_usecase import (
    SendStartupNotificationUsecase,
)
from .infrastructure.adapters.line_adapter import LineMessagingAdapter
from .infrastructure.logger import create_logger

load_dotenv()

app = Flask(__name__)
logger = create_logger(__name__)

CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")

# Gunicorn 前提。ここで必要な初期化のみ行う。

_line_adapter = LineMessagingAdapter(logger=logger)
_line_adapter.init(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
bind_routes(app, handler, _line_adapter)

logger.info("App initialized (module imported)")


def _notify_once_on_import() -> None:
    """インポート時に一度だけ起動通知を送る。

    環境変数 DISABLE_STARTUP_NOTIFICATION=1 で無効化可能。
    コンテナ内で一度だけ実行されるよう、/tmp配下のフラグファイルで多重送信を防止。
    """
    if os.environ.get("DISABLE_STARTUP_NOTIFICATION") == "1":
        logger.info("Startup notification is disabled by environment variable")
        return

    flag_path = "/tmp/line-bot-startup-notified"
    try:
        with open(flag_path, "x"):
            pass
    except FileExistsError:
        logger.debug("Startup notification already sent (flag file exists)")
        return

    try:
        startup_notification_usecase = SendStartupNotificationUsecase(
            _line_adapter, create_logger(__name__)
        )
        startup_notification_usecase.execute()
        logger.info("Startup notification sent successfully")
    except Exception as e:
        logger.error(f"startup notify failed: {e}")


_notify_once_on_import()
