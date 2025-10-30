from typing import Any, Optional, Protocol


class LineAdapterProtocol(Protocol):
    # reply_message は SDK のモデルや dict を受け取るため、柔軟に受けられるようにする。
    # エディタの型チェックでテスト用のフェイク関数が弾かれるのを避けるため
    # 可変引数を許容します。
    def reply_message(self, *args: Any, **kwargs: Any) -> Any:
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
