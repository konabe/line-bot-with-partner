import os
from dotenv import load_dotenv
from flask import Flask
from linebot.v3.webhook import WebhookHandler
from .infrastructure import init_messaging_api, safe_reply_message, safe_push_message
from .application.handler_registration import register_handlers
from .application.startup_notify import notify_startup_if_configured
from .infrastructure.logger import create_logger

load_dotenv()

app = Flask(__name__)
logger = create_logger(__name__)

CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')

init_messaging_api(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# register handlers from application layer
register_handlers(app, handler, safe_reply_message)

# Gunicorn 環境では __main__ ブロックは実行されないため、ここで初期化ログを出す
logger.info("App initialized (module imported)")

def _notify_once_on_import() -> None:
    """インポート時に一度だけ起動通知を送る。

    - Gunicorn 前提のため __main__ は実行されない。
    - コンテナ内で一度だけ実行されるよう、固定フラグファイルで多重送信を防止。
    """
    flag_path = "/tmp/line-bot-startup-notified"
    try:
        with open(flag_path, "x"):
            pass
    except FileExistsError:
        return
    try:
        notify_startup_if_configured(safe_push_message, logger)
    except Exception as e:
        logger.error(f"startup notify failed: {e}")


_notify_once_on_import()
