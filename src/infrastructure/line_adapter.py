import logging
from . import messaging as infra_messaging
from ..ports.messaging import MessagingPort

logger = logging.getLogger(__name__)


class LineMessagingAdapter(MessagingPort):
    def __init__(self):
        self.messaging_api = None

    def init(self, access_token: str):
        try:
            from linebot.v3.messaging.configuration import Configuration
            from linebot.v3.messaging.api_client import ApiClient
            from linebot.v3.messaging import MessagingApi
            _config = Configuration(access_token=access_token)
            _api_client = ApiClient(configuration=_config)
            self.messaging_api = MessagingApi(_api_client)
        except Exception as e:
            self.messaging_api = None
            logger.error(f"Failed to initialize LineMessagingAdapter: {e}")

    def reply_message(self, reply_message_request):
        if self.messaging_api is None:
            logger.warning("messaging_api is not initialized; skipping reply_message")
            return
        try:
            try:
                logger.debug(f"reply payload: {reply_message_request.to_dict()}")
            except Exception:
                logger.debug("reply payload: <unable to serialize>")
            self.messaging_api.reply_message(reply_message_request)
        except Exception as e:
            logger.error(f"Error when calling messaging_api.reply_message: {e}")

    def push_message(self, push_message_request):
        if self.messaging_api is None:
            logger.warning("messaging_api is not initialized; skipping push_message")
            return
        try:
            try:
                logger.debug(f"push payload: {push_message_request.to_dict()}")
            except Exception:
                logger.debug("push payload: <unable to serialize>")
            self.messaging_api.push_message(push_message_request)
        except Exception as e:
            logger.error(f"Error when calling messaging_api.push_message: {e}")
