from typing import Protocol


class LineAdapterProtocol(Protocol):
    def reply_message(self, req) -> None:
        ...


class OpenAIAdapterProtocol(Protocol):
    def get_chatgpt_response(self, user_message: str) -> str:
        ...
