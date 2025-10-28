from abc import ABC, abstractmethod
from typing import Optional


class MessagingPort(ABC):
    """Abstract port for messaging infrastructure (adapter interface)."""

    @abstractmethod
    def init(self, access_token: str):
        raise NotImplementedError()

    @abstractmethod
    def reply_message(self, reply_message_request):
        raise NotImplementedError()

    @abstractmethod
    def push_message(self, push_message_request):
        raise NotImplementedError()

    @abstractmethod
    def get_display_name_from_line_profile(self, user_id: str) -> Optional[str]:
        raise NotImplementedError()
