import os
import logging
from dotenv import load_dotenv
from flask import Flask

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')

from linebot.v3.webhook import WebhookHandler
from .infrastructure import init_messaging_api, safe_reply_message, safe_push_message
from .application.handlers import register_handlers
from .application.startup_notify import notify_startup_if_configured

init_messaging_api(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# register handlers from application layer
register_handlers(app, handler, safe_reply_message, safe_push_message)

if __name__ == '__main__':
    logger.info("Flask app starting...")
    notify_startup_if_configured(safe_push_message, logger)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
