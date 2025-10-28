"""Mock messaging adapter for tests.

This adapter records replies and pushes in memory so unit tests can assert on
them without calling external APIs.
"""

from typing import Any, List


class MockMessagingAdapter:
    """In-memory messaging adapter used for tests.

    Usage in tests:
        from tests.support.mock_adapter import MockMessagingAdapter

        mock = MockMessagingAdapter()
        mock.init('test-token')

    Then assert on mock.get_replies() / mock.get_pushes().
    """

    def __init__(self) -> None:
        self.access_token: str | None = None
        self._replies: List[Any] = []
        self._pushes: List[Any] = []
        self.inited: bool = False

    def init(self, access_token: str):
        self.access_token = access_token
        self.inited = True

    def reply_message(self, reply_message_request):
        # Store the request object as-is so tests can inspect attributes.
        self._replies.append(reply_message_request)

    def push_message(self, push_message_request):
        self._pushes.append(push_message_request)

    def get_display_name_from_line_profile(self, user_id: str) -> str | None:
        # Mock implementation - returns a test display name
        return f"TestUser_{user_id}" if user_id else None

    # Helper methods for tests
    def get_replies(self) -> List[Any]:
        return list(self._replies)

    def get_pushes(self) -> List[Any]:
        return list(self._pushes)

    def reset(self) -> None:
        self._replies.clear()
        self._pushes.clear()


__all__ = ["MockMessagingAdapter"]
