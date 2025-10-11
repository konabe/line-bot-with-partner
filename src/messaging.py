import logging
from linebot.v3.messaging import MessagingApi
from linebot.v3.messaging.api_client import ApiClient
from linebot.v3.messaging.configuration import Configuration

logger = logging.getLogger(__name__)

messaging_api = None


def init_messaging_api(access_token: str):
    global messaging_api
    try:
        _config = Configuration(access_token=access_token)
        _api_client = ApiClient(configuration=_config)
        messaging_api = MessagingApi(_api_client)
    except Exception as e:
        messaging_api = None
        logger.error(f"Failed to initialize MessagingApi: {e}")


def safe_reply_message(reply_message_request):
    if messaging_api is None:
        logger.warning("messaging_api is not initialized; skipping reply_message")
        return
    try:
        try:
            logger.debug(f"reply payload: {reply_message_request.to_dict()}")
        except Exception:
            logger.debug("reply payload: <unable to serialize>")
        messaging_api.reply_message(reply_message_request)
    except Exception as e:
        logger.error(f"Error when calling messaging_api.reply_message: {e}")


def safe_push_message(push_message_request):
    if messaging_api is None:
        logger.warning("messaging_api is not initialized; skipping push_message")
        return
    try:
        try:
            logger.debug(f"push payload: {push_message_request.to_dict()}")
        except Exception:
            logger.debug("push payload: <unable to serialize>")
        messaging_api.push_message(push_message_request)
    except Exception as e:
        logger.error(f"Error when calling messaging_api.push_message: {e}")
