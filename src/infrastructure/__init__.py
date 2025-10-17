"""Infrastructure layer package.

Adapters for external systems (LINE Messaging API, HTTP clients, etc.)
This module manages a pluggable messaging adapter implementing the MessagingPort.
"""

import logging
import os
import time
import threading
from typing import Optional
from ..ports.messaging import MessagingPort

logger = logging.getLogger(__name__)


class MessagingInfrastructure:
    """メッセージングインフラを管理するクラス"""

    def __init__(self):
        self._adapter: Optional[MessagingPort] = None

    def register_adapter(self, adapter: MessagingPort):
        self._adapter = adapter

    def init_messaging_api(self, access_token: str):
        if self._adapter is None:
            # lazy import default adapter
            try:
                logger.debug("No messaging adapter registered, attempting to import LineMessagingAdapter")
                from .line_adapter import LineMessagingAdapter
                self.register_adapter(LineMessagingAdapter())
                logger.info("LineMessagingAdapter registered")
            except Exception as e:
                logger.error(f"Failed to import/register LineMessagingAdapter: {e}")
                return
        try:
            if not access_token:
                logger.warning("init_messaging_api called with empty access_token; adapter init may fail")
            self._adapter.init(access_token)
            logger.debug("_adapter.init called")
        except Exception as e:
            logger.error(f"Exception while initializing messaging adapter: {e}")

    def safe_reply_message(self, reply_message_request, fallback_to: str = None) -> bool:
        """Attempt to reply using the messaging adapter. Returns True on success.

        If reply fails with an invalid/expired reply token, and fallback_to is provided,
        attempt to send a push message to the fallback destination.
        """
        if self._adapter is None:
            logger.warning("safe_reply_message called but no messaging adapter is registered; skipping reply")
            return False
        try:
            self._adapter.reply_message(reply_message_request)
            return True
        except Exception as e:
            # Per user request: on reply failure, only log the error and do not retry or fallback.
            logger.error(f"safe_reply_message failed (no fallback): {e}")
            return False

    def safe_push_message(self, push_message_request):
        if self._adapter is None:
            logger.warning("safe_push_message called but no messaging adapter is registered; skipping push")
            return
        try:
            self._adapter.push_message(push_message_request)
        except Exception as e:
            logger.error(f"Exception in safe_push_message: {e}")
            return


# シングルトンインスタンス
_messaging_infrastructure = MessagingInfrastructure()


def register_adapter(adapter: MessagingPort):
    _messaging_infrastructure.register_adapter(adapter)


def init_messaging_api(access_token: str):
    _messaging_infrastructure.init_messaging_api(access_token)


def safe_reply_message(reply_message_request, fallback_to: str = None) -> bool:
    return _messaging_infrastructure.safe_reply_message(reply_message_request, fallback_to)


def safe_push_message(push_message_request):
    _messaging_infrastructure.safe_push_message(push_message_request)

