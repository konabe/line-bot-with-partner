from typing import Any, Optional, Protocol


class LineAdapterProtocol(Protocol):
    # 実装側の LineMessagingAdapter.reply_message は
    # `reply_message(self, reply_message_request)` を受け取るため、名前を一致させます。
    def reply_message(self, reply_message_request: Any) -> None:
        ...

    # 実装は存在しない/失敗する場合 None を返すため Optional[str] にします。
    def get_display_name_from_line_profile(self, user_id: str) -> Optional[str]:
        ...


class OpenAIAdapterProtocol(Protocol):
    def get_chatgpt_response(self, user_message: str) -> str:
        ...

    def get_chatgpt_meal_suggestion(self) -> str:
        ...


class WeatherAdapterProtocol(Protocol):
    def get_weather_text(self, location: str) -> str:
        ...
