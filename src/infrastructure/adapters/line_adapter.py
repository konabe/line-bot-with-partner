from typing import Optional

from linebot.v3.messaging import MessagingApi
from linebot.v3.messaging.api_client import ApiClient
from linebot.v3.messaging.configuration import Configuration

from ..logger import Logger, create_logger


class LineMessagingAdapter:
    def __init__(self, logger: Optional[Logger] = None):
        self.logger: Logger = logger or create_logger(__name__)
        self.messaging_api = None

    def init(self, access_token: str):
        try:
            config = Configuration(access_token=access_token)
            api_client = ApiClient(configuration=config)
            self.messaging_api = MessagingApi(api_client)
        except Exception as e:
            self.messaging_api = None
            self.logger.error(f"Failed to initialize LineMessagingAdapter: {e}")

    def reply_message(self, reply_message_request):
        if self.messaging_api is None:
            self.logger.warning(
                "messaging_api is not initialized; skipping reply_message"
            )
            return

        self._log_payload(reply_message_request, "reply")

        try:
            self.messaging_api.reply_message(reply_message_request)
        except Exception as e:
            self.logger.error(f"Error when calling messaging_api.reply_message: {e}")
            raise

    def push_message(self, push_message_request):
        if self.messaging_api is None:
            self.logger.warning(
                "messaging_api is not initialized; skipping push_message"
            )
            return

        self._log_payload(push_message_request, "push")

        try:
            self.messaging_api.push_message(push_message_request)
        except Exception as e:
            self.logger.error(f"Error when calling messaging_api.push_message: {e}")
            raise

    def get_display_name_from_line_profile(self, user_id: str) -> Optional[str]:
        if self.messaging_api is None:
            self.logger.debug(
                "messaging_api is not initialized; skipping profile fetch"
            )
            return None

        if not user_id:
            self.logger.debug("user_id is empty; skipping profile fetch")
            return None

        try:
            profile = self.messaging_api.get_profile(user_id)
            return profile.display_name
        except Exception as e:
            self.logger.error(f"Failed to fetch profile for {user_id}: {e}")
            return None

    def _log_payload(self, request, message_type: str):
        """リクエストのペイロードをログ出力する"""
        try:
            payload = request.to_dict()
        except Exception:
            try:
                payload = request.dict(by_alias=True, exclude_none=True)
            except Exception:
                self.logger.debug(f"{message_type} payload: <unable to serialize>")
                return

        self.logger.debug(f"{message_type} payload: {payload}")


__all__ = ["LineMessagingAdapter"]
