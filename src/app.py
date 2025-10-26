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

# Gunicorn 環境では __main__ ブロックは実行されない

init_messaging_api(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
register_handlers(app, handler, safe_reply_message)

notify_startup_if_configured(safe_push_message, logger)
app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
logger.info("App initialized (module imported)")
