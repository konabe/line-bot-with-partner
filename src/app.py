import os

from dotenv import load_dotenv
from flask import Flask
from linebot.v3.webhook import WebhookHandler

from .application.handler_registration import register_handlers
from .application.startup_notify import notify_startup_if_configured
from .infrastructure.adapters.line_adapter import LineMessagingAdapter
from .infrastructure.logger import create_logger

load_dotenv()

app = Flask(__name__)
logger = create_logger(__name__)

CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")

# Gunicorn 前提。ここで必要な初期化のみ行う。

# Create a messaging infrastructure instance and initialize the messaging API.
# Callers will use the instance's bound methods (no package-level wrappers).
# Create a Line adapter instance and initialize the messaging API directly.
_line_adapter = LineMessagingAdapter(logger=logger)
_line_adapter.init(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
register_handlers(app, handler, _line_adapter.reply_message, _line_adapter)

logger.info("App initialized (module imported)")


def _notify_once_on_import() -> None:
    """インポート時に一度だけ起動通知を送る。

    コンテナ内で一度だけ実行されるよう、固定フラグファイルで多重送信を防止。
    """
    flag_path = "/tmp/line-bot-startup-notified"
    try:
        with open(flag_path, "x"):
            pass
    except FileExistsError:
        return
    try:
        notify_startup_if_configured(_line_adapter.push_message, logger)
    except Exception as e:
        logger.error(f"startup notify failed: {e}")


_notify_once_on_import()
