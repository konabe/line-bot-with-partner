import logging
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
            # We assume reply_message is called with SDK model instances
            # (pydantic models or SDK models). Simply pass the model through to
            # the SDK. For logging, try to obtain a serializable dict.
            try:
                payload_for_log = None
                try:
                    payload_for_log = reply_message_request.to_dict()
                except Exception:
                    try:
                        payload_for_log = reply_message_request.dict(by_alias=True, exclude_none=True)
                    except Exception:
                        payload_for_log = None
                try:
                    logger.debug(f"reply payload: {payload_for_log}")
                except Exception:
                    logger.debug("reply payload: <unable to serialize>")

                # Directly send the model/request object to the SDK
                self.messaging_api.reply_message(reply_message_request)
                return
            except Exception:
                # As a last-resort safety net, attempt to serialize and build
                # a ReplyMessageRequest via parse_obj and send that.
                try:
                    from linebot.v3.messaging import models
                    sdk_req = models.ReplyMessageRequest.parse_obj(reply_message_request)
                    self.messaging_api.reply_message(sdk_req)
                    return
                except Exception:
                    # Give up and re-raise the original error to let caller handle
                    raise
        except Exception as e:
            logger.error(f"Error when calling messaging_api.reply_message: {e}")
            # re-raise so caller (safe_reply_message) can react (e.g. fallback to push)
            raise

    def push_message(self, push_message_request):
        if self.messaging_api is None:
            logger.warning("messaging_api is not initialized; skipping push_message")
            return
        try:
            # Assume push_message is called with SDK model instances (PushMessageRequest
            # or other SDK models). Send the model directly; try to log its dict
            # representation first. If sending fails, attempt to parse into
            # PushMessageRequest and resend as a fallback.
            try:
                try:
                    logger.debug(f"push payload: {push_message_request.to_dict()}")
                except Exception:
                    try:
                        logger.debug(f"push payload: {push_message_request.dict(by_alias=True, exclude_none=True)}")
                    except Exception:
                        logger.debug("push payload: <unable to serialize>")

                self.messaging_api.push_message(push_message_request)
                return
            except Exception:
                # Fallback: try to build a PushMessageRequest from the object
                try:
                    from linebot.v3.messaging import models
                    sdk_req = models.PushMessageRequest.parse_obj(push_message_request)
                    self.messaging_api.push_message(sdk_req)
                    return
                except Exception:
                    # Re-raise the original exception to let caller handle it
                    raise
        except Exception as e:
            logger.error(f"Error when calling messaging_api.push_message: {e}")
            raise
