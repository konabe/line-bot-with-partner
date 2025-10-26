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
            # Accept several kinds of inputs:
            # - dict payload matching LINE Messaging API (preferred for flex messages)
            # - SDK model instances (have .to_dict or .dict)
            # - ReplyMessageRequest pydantic model
            final_payload = None
            original = reply_message_request
            # If user passed a dict, use it directly
            if isinstance(reply_message_request, dict):
                final_payload = reply_message_request
            else:
                # Try to call to_dict() (SDK models / ReplyMessageRequest)
                try:
                    final_payload = reply_message_request.to_dict()
                except Exception:
                    # Try pydantic dict()
                    try:
                        final_payload = reply_message_request.dict(by_alias=True, exclude_none=True)
                    except Exception:
                        final_payload = None

            # If serialization produced a payload missing flex fields, but the
            # original argument was a dict-like that contains them, prefer the
            # original dict to preserve altText/contents for flex messages.
            if final_payload and 'messages' in final_payload:
                for idx, m in enumerate(final_payload.get('messages', [])):
                    if isinstance(m, dict) and m.get('type') == 'flex':
                        # Check presence of required flex fields
                        if not m.get('altText') or not m.get('contents'):
                            # If original was dict and had complete fields, prefer it
                            if isinstance(original, dict):
                                final_payload = original
                                break

            try:
                logger.debug(f"reply payload: {final_payload}")
            except Exception:
                logger.debug("reply payload: <unable to serialize>")

            # Use the SDK messaging_api exclusively. If caller provided a dict
            # payload (preferred for flex), pass it through to the SDK's
            # reply_message. Avoid direct HTTP requests from this adapter.
            if isinstance(final_payload, dict):
                self.messaging_api.reply_message(final_payload)
            else:
                self.messaging_api.reply_message(reply_message_request)
        except Exception as e:
            logger.error(f"Error when calling messaging_api.reply_message: {e}")
            # re-raise so caller (safe_reply_message) can react (e.g. fallback to push)
            raise

    def push_message(self, push_message_request):
        if self.messaging_api is None:
            logger.warning("messaging_api is not initialized; skipping push_message")
            return
        try:
            # Prefer SDK messaging_api for push; accept dict payloads and
            # pass them through to the SDK as-is.
            if isinstance(push_message_request, dict):
                self.messaging_api.push_message(push_message_request)
            else:
                try:
                    logger.debug(f"push payload: {push_message_request.to_dict()}")
                except Exception:
                    logger.debug("push payload: <unable to serialize>")
                self.messaging_api.push_message(push_message_request)
        except Exception as e:
            logger.error(f"Error when calling messaging_api.push_message: {e}")
            raise
