import os
from typing import Optional

from ..logger import Logger, create_logger


class LineMessagingAdapter:
    def __init__(self, logger: Optional[Logger] = None):
        self.logger: Logger = logger or create_logger(__name__)
        self.messaging_api = None

    def init(self, access_token: str):
        try:
            from linebot.v3.messaging import MessagingApi
            from linebot.v3.messaging.api_client import ApiClient
            from linebot.v3.messaging.configuration import Configuration

            _config = Configuration(access_token=access_token)
            _api_client = ApiClient(configuration=_config)
            self.messaging_api = MessagingApi(_api_client)
        except Exception as e:
            self.messaging_api = None
            self.logger.error(f"Failed to initialize LineMessagingAdapter: {e}")

    def reply_message(self, reply_message_request):
        if self.messaging_api is None:
            self.logger.warning(
                "messaging_api is not initialized; skipping reply_message"
            )
            return
        try:
            try:
                payload_for_log = None
                try:
                    payload_for_log = reply_message_request.to_dict()
                except Exception:
                    try:
                        payload_for_log = reply_message_request.dict(
                            by_alias=True, exclude_none=True
                        )
                    except Exception:
                        payload_for_log = None
                try:
                    self.logger.debug(f"reply payload: {payload_for_log}")
                except Exception:
                    self.logger.debug("reply payload: <unable to serialize>")

                self.messaging_api.reply_message(reply_message_request)
                return
            except Exception:
                try:
                    from linebot.v3.messaging import models

                    sdk_req = models.ReplyMessageRequest.parse_obj(
                        reply_message_request
                    )
                    self.messaging_api.reply_message(sdk_req)
                    return
                except Exception:
                    raise
        except Exception as e:
            self.logger.error(f"Error when calling messaging_api.reply_message: {e}")
            raise

    def push_message(self, push_message_request):
        if self.messaging_api is None:
            self.logger.warning(
                "messaging_api is not initialized; skipping push_message"
            )
            return
        try:
            try:
                try:
                    self.logger.debug(f"push payload: {push_message_request.to_dict()}")
                except Exception:
                    try:
                        self.logger.debug(
                            f"push payload: {push_message_request.dict(by_alias=True, exclude_none=True)}"
                        )
                    except Exception:
                        self.logger.debug("push payload: <unable to serialize>")

                self.messaging_api.push_message(push_message_request)
                return
            except Exception:
                try:
                    from linebot.v3.messaging import models

                    sdk_req = models.PushMessageRequest.parse_obj(push_message_request)
                    self.messaging_api.push_message(sdk_req)
                    return
                except Exception:
                    raise
        except Exception as e:
            self.logger.error(f"Error when calling messaging_api.push_message: {e}")
            raise

    def get_display_name_from_line_profile(self, user_id: str) -> Optional[str]:
        try:
            import requests
        except Exception:
            self.logger.debug("requests not available; skipping profile fetch")
            return None

        token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
        if not token or not user_id:
            self.logger.debug(
                "LINE_CHANNEL_ACCESS_TOKEN not set or empty; skipping profile fetch"
            )
            return None

        try:
            resp = requests.get(
                f"https://api.line.me/v2/bot/profile/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=2,
            )
            if resp.status_code == 200:
                return resp.json().get("displayName")
            self.logger.debug(
                f"profile fetch returned status {resp.status_code} for {user_id}"
            )
        except Exception as e:
            self.logger.error(f"Failed to fetch profile for {user_id}: {e}")
        return None


__all__ = ["LineMessagingAdapter"]
