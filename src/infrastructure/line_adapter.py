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
            # payload (preferred for flex), try to construct the SDK's
            # ReplyMessageRequest model from the dict so SDK serialization is
            # consistent. If model construction fails, fall back to passing the
            # dict through (the SDK may still accept dicts).
            if isinstance(final_payload, dict):
                # If messaging_api looks like the real SDK, build the
                # ReplyMessageRequest model to ensure proper serialization.
                # Otherwise (tests, fakes), pass the dict through unchanged.
                try:
                    is_sdk = getattr(self.messaging_api.__class__, '__module__', '').startswith('linebot.v3')
                except Exception:
                    is_sdk = False

                if is_sdk:
                    try:
                        # Build SDK models for each message to ensure required
                        # fields (text, altText, contents) are present when
                        # serialized by the SDK.
                        from linebot.v3.messaging import models

                        msgs = []
                        for m in final_payload.get('messages', []):
                            if not isinstance(m, dict):
                                msgs.append(m)
                                continue
                            mtype = m.get('type')
                            if mtype == 'text':
                                try:
                                    msgs.append(models.TextMessage(text=m.get('text')))
                                except Exception:
                                    msgs.append(m)
                            elif mtype == 'flex':
                                try:
                                    contents = m.get('contents')
                                    # Try to parse bubble contents to FlexBubble
                                    if isinstance(contents, dict):
                                        bubble = models.FlexBubble.parse_obj(contents)
                                    else:
                                        bubble = contents
                                    flex_msg = models.FlexMessage(altText=m.get('altText', ''), contents=bubble)
                                    msgs.append(flex_msg)
                                except Exception:
                                    try:
                                        msgs.append(models.FlexMessage.parse_obj(m))
                                    except Exception:
                                        msgs.append(m)
                            else:
                                try:
                                    msgs.append(models.Message.parse_obj(m))
                                except Exception:
                                    msgs.append(m)

                        # Construct ReplyMessageRequest with snake_case args
                        reply_token = final_payload.get('replyToken') or final_payload.get('reply_token')
                        notification_disabled = final_payload.get('notificationDisabled', final_payload.get('notification_disabled', False))
                        try:
                            sdk_req = models.ReplyMessageRequest(reply_token=reply_token, messages=msgs, notification_disabled=notification_disabled)
                            self.messaging_api.reply_message(sdk_req)
                        except Exception:
                            # Fallback to parse_obj which may accept camelCase dict
                            try:
                                sdk_req = models.ReplyMessageRequest.parse_obj(final_payload)
                                self.messaging_api.reply_message(sdk_req)
                            except Exception:
                                # Last resort: pass original dict
                                self.messaging_api.reply_message(final_payload)
                    except Exception:
                        # If building SDK models failed entirely, pass dict through
                        self.messaging_api.reply_message(final_payload)
                else:
                    # Keep previous behavior for test fakes and other non-SDK adapters
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
            # Prefer SDK messaging_api for push; if caller provided a dict
            # try to construct PushMessageRequest so SDK serializes it
            # consistently. Fall back to passing the dict through if needed.
            if isinstance(push_message_request, dict):
                try:
                    is_sdk = getattr(self.messaging_api.__class__, '__module__', '').startswith('linebot.v3')
                except Exception:
                    is_sdk = False

                if is_sdk:
                    try:
                        from linebot.v3.messaging import models

                        msgs = []
                        for m in push_message_request.get('messages', []):
                            if not isinstance(m, dict):
                                msgs.append(m)
                                continue
                            mtype = m.get('type')
                            if mtype == 'text':
                                try:
                                    msgs.append(models.TextMessage(text=m.get('text')))
                                except Exception:
                                    msgs.append(m)
                            elif mtype == 'flex':
                                try:
                                    contents = m.get('contents')
                                    if isinstance(contents, dict):
                                        bubble = models.FlexBubble.parse_obj(contents)
                                    else:
                                        bubble = contents
                                    flex_msg = models.FlexMessage(altText=m.get('altText', ''), contents=bubble)
                                    msgs.append(flex_msg)
                                except Exception:
                                    try:
                                        msgs.append(models.FlexMessage.parse_obj(m))
                                    except Exception:
                                        msgs.append(m)
                            else:
                                try:
                                    msgs.append(models.Message.parse_obj(m))
                                except Exception:
                                    msgs.append(m)

                        to = push_message_request.get('to')
                        notification_disabled = push_message_request.get('notificationDisabled', push_message_request.get('notification_disabled', False))
                        try:
                            sdk_req = models.PushMessageRequest(to=to, messages=msgs, notification_disabled=notification_disabled)
                            self.messaging_api.push_message(sdk_req)
                        except Exception:
                            try:
                                sdk_req = models.PushMessageRequest.parse_obj(push_message_request)
                                self.messaging_api.push_message(sdk_req)
                            except Exception:
                                self.messaging_api.push_message(push_message_request)
                    except Exception:
                        self.messaging_api.push_message(push_message_request)
                else:
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
