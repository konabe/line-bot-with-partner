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


def safe_reply_message(reply_message_request):
    if _adapter is None:
        logger.warning("safe_reply_message called but no messaging adapter is registered; skipping reply")
        return
    try:
        _adapter.reply_message(reply_message_request)
    except Exception as e:
        logger.error(f"Exception in safe_reply_message: {e}")
        return


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

