"""Infrastructure layer package.

Adapters for external systems (LINE Messaging API, HTTP clients, etc.)
This module manages a pluggable messaging adapter implementing the MessagingPort.
"""

import logging
from typing import Optional
from ..ports.messaging import MessagingPort

logger = logging.getLogger(__name__)

_adapter: Optional[MessagingPort] = None


def register_adapter(adapter: MessagingPort):
    global _adapter
    _adapter = adapter


def init_messaging_api(access_token: str):
    if _adapter is None:
        # lazy import default adapter
        try:
            logger.debug("No messaging adapter registered, attempting to import LineMessagingAdapter")
            from .line_adapter import LineMessagingAdapter
            register_adapter(LineMessagingAdapter())
            logger.info("LineMessagingAdapter registered")
        except Exception as e:
            logger.error(f"Failed to import/register LineMessagingAdapter: {e}")
            return
    try:
        if not access_token:
            logger.warning("init_messaging_api called with empty access_token; adapter init may fail")
        _adapter.init(access_token)
        logger.debug("_adapter.init called")
    except Exception as e:
        logger.error(f"Exception while initializing messaging adapter: {e}")


def safe_reply_message(reply_message_request, fallback_to: str = None) -> bool:
    """Attempt to reply using the messaging adapter. Returns True on success.

    If reply fails with an invalid/expired reply token, and fallback_to is provided,
    attempt to send a push message to the fallback destination.
    """
    if _adapter is None:
        logger.warning("safe_reply_message called but no messaging adapter is registered; skipping reply")
        return False
    try:
        _adapter.reply_message(reply_message_request)
        return True
    except Exception as e:
        logger.error(f"Exception in safe_reply_message: {e}")
        # inspect exception message to detect invalid reply token
        if fallback_to:
            try:
                logger.info(f"Attempting fallback push to {fallback_to} due to reply failure")
                from linebot.v3.messaging.models import PushMessageRequest, TextMessage
                push_message_request = PushMessageRequest(
                    to=fallback_to,
                    messages=[TextMessage(text='返信に失敗しました。こちらで通知します。')]
                )
                try:
                    _adapter.push_message(push_message_request)
                    logger.info("Fallback push succeeded")
                except Exception as push_err:
                    logger.error(f"Fallback push failed: {push_err}")
            except Exception as ex:
                logger.error(f"Failed to perform fallback push: {ex}")
        return False


def safe_push_message(push_message_request):
    if _adapter is None:
        logger.warning("safe_push_message called but no messaging adapter is registered; skipping push")
        return
    try:
        _adapter.push_message(push_message_request)
    except Exception as e:
        logger.error(f"Exception in safe_push_message: {e}")
        return


__all__ = [
    'register_adapter',
    'init_messaging_api',
    'safe_reply_message',
    'safe_push_message',
]

