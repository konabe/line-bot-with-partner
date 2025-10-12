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
from .messaging import init_messaging_api
from .infrastructure import safe_reply_message, safe_push_message
from .application.handlers import register_handlers

init_messaging_api(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# register handlers from application layer
register_handlers(app, handler, safe_reply_message, safe_push_message)

if __name__ == '__main__':
    logger.info("Flask app starting...")
    # 起動時に管理者へ通知（環境変数 ADMIN_USER_ID にユーザーIDを設定）
    try:
        admin_id = os.environ.get('ADMIN_USER_ID')
        if admin_id:
            try:
                from linebot.v3.messaging.models import PushMessageRequest, TextMessage
                push_message_request = PushMessageRequest(
                    to=admin_id,
                    messages=[TextMessage(text='サーバーが起動しました。')]
                )
                safe_push_message(push_message_request)
                logger.info(f"startup notification sent to admin {admin_id}")
            except Exception as e:
                logger.error(f"failed to send startup notification: {e}")
        else:
            logger.debug('ADMIN_USER_ID not set; skipping startup notification')
    except Exception as e:
        logger.error(f"unexpected error during startup notification: {e}")

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
