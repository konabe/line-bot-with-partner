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


def _env_true(val: str | None) -> bool:
    return bool(val) and val.lower() in ("1", "true", "yes", "on")


def _notify_once_on_import() -> None:
    if not _env_true(os.environ.get("STARTUP_NOTIFY_ON_IMPORT")):
        return
    flag_path = os.environ.get("STARTUP_NOTIFY_FLAG_PATH", "/tmp/line-bot-startup-notified")
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

if __name__ == '__main__':
    logger.info("Flask app starting...")
    notify_startup_if_configured(safe_push_message, logger)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
