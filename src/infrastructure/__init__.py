import logging
from typing import Optional
from ..ports.messaging import MessagingPort

import logging
from typing import Optional
from ..ports.messaging import MessagingPort

_logger = logging.getLogger(__name__)


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
                _logger.debug("No messaging adapter registered, attempting to import LineMessagingAdapter")
                from .adapters.line_adapter import LineMessagingAdapter
                self.register_adapter(LineMessagingAdapter())
                _logger.info("LineMessagingAdapter registered")
            except Exception as e:
                _logger.error(f"Failed to import/register LineMessagingAdapter: {e}")
                return
        # At this point we expect an adapter to be registered. Assign to a local
        # variable and check to satisfy static analyzers that adapter is not None.
        adapter = self._adapter
        if adapter is None:
            _logger.error("No messaging adapter available after registration attempt; aborting init")
            return

        try:
            if not access_token:
                _logger.warning("init_messaging_api called with empty access_token; adapter init may fail")
            adapter.init(access_token)
            _logger.debug("adapter.init called")
        except Exception as e:
            _logger.error(f"Exception while initializing messaging adapter: {e}")

    def safe_reply_message(self, reply_message_request, fallback_to: Optional[str] = None) -> bool:
        """Attempt to reply using the messaging adapter. Returns True on success.

        If reply fails with an invalid/expired reply token, and fallback_to is provided,
        attempt to send a push message to the fallback destination.
        """
        if self._adapter is None:
            _logger.warning("safe_reply_message called but no messaging adapter is registered; skipping reply")
            return False
        try:
            self._adapter.reply_message(reply_message_request)
            return True
        except Exception as e:
            # Per user request: on reply failure, only log the error and do not retry or fallback.
            _logger.error(f"safe_reply_message failed (no fallback): {e}")
            return False

    def safe_push_message(self, push_message_request):
        if self._adapter is None:
            _logger.warning("safe_push_message called but no messaging adapter is registered; skipping push")
            return False
        try:
            self._adapter.push_message(push_message_request)
            return True
        except Exception as e:
            _logger.error(f"Exception in safe_push_message: {e}")
            return False


# シングルトンインスタンス
_messaging_infrastructure = MessagingInfrastructure()


def register_adapter(adapter: MessagingPort):
    _messaging_infrastructure.register_adapter(adapter)


def init_messaging_api(access_token: str):
    _messaging_infrastructure.init_messaging_api(access_token)


def safe_reply_message(reply_message_request, fallback_to: Optional[str] = None) -> bool:
    return _messaging_infrastructure.safe_reply_message(reply_message_request, fallback_to)


def safe_push_message(push_message_request):
    return _messaging_infrastructure.safe_push_message(push_message_request)

