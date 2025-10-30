from typing import Any, Optional, Protocol


class LineAdapterProtocol(Protocol):
    def reply_message(self, *args: Any, **kwargs: Any) -> Any:
        ...

    def push_message(self, *args: Any, **kwargs: Any) -> Optional[bool]:
        ...

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
