from typing import TYPE_CHECKING, Optional, Protocol

if TYPE_CHECKING:
    from src.domain.models.digimon_info import DigimonInfo
    from src.domain.models.pokemon_info import PokemonInfo


class LineAdapterProtocol(Protocol):
    def reply_message(self, reply_message_request) -> None: ...

    def push_message(self, push_message_request) -> None: ...

    def get_display_name_from_line_profile(self, user_id: str) -> Optional[str]: ...


class OpenAIAdapterProtocol(Protocol):
    def get_chatgpt_response(self, user_message: str) -> str: ...

    def generate_image(self, prompt: str) -> Optional[str]: ...

    def generate_image_prompt(self, requirements: str) -> str: ...

    def get_chatgpt_meal_suggestion(
        self, return_request_id: bool = False
    ) -> str | tuple[str, Optional[int]]: ...

    def track_score(
        self, request_id: int, score: int, score_name: str = "user_feedback"
    ) -> bool: ...


class WeatherAdapterProtocol(Protocol):
    def get_weather_text(self, location: str) -> str: ...


class DigimonAdapterProtocol(Protocol):
    def get_random_digimon_info(self) -> Optional["DigimonInfo"]: ...


class PokemonAdapterProtocol(Protocol):
    def get_random_pokemon_info(self) -> Optional["PokemonInfo"]: ...


class JankenServiceProtocol(Protocol):
    def play_and_make_reply(self, user_hand_input: str, user_label: str) -> str: ...
