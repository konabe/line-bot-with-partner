import os
import re
from typing import Optional

from linebot.v3.webhooks.models.message_event import MessageEvent

from .base_usecase import BaseUsecase
from .protocols import LineAdapterProtocol, WeatherAdapterProtocol


class SendWeatherUsecase(BaseUsecase):
    def __init__(
        self, line_adapter: LineAdapterProtocol, weather_adapter: WeatherAdapterProtocol
    ):
        super().__init__(line_adapter)
        self._weather_adapter = weather_adapter

    def execute(self, event: MessageEvent, text: str) -> None:
        self._validate_reply_token(event)

        reply_text = self._get_weather_reply_text(text)
        if event.reply_token:
            self._send_text_reply(event.reply_token, reply_text)

    def _get_weather_reply_text(self, text: str) -> str:
        t = text.strip()

        if t == "天気":
            return self._get_multiple_cities_weather()
        else:
            location = self._extract_location_from_weather_query(text)
            return self._get_single_city_weather(location)

    def _get_multiple_cities_weather(self) -> str:
        weather_locations = os.environ.get("WEATHER_LOCATIONS")
        if not weather_locations:
            return "表示する都市が設定されていません。環境変数 WEATHER_LOCATIONS にカンマ区切りの都市名を設定してください。"

        cities = self._parse_weather_locations(weather_locations)
        if not cities:
            return "表示する都市が設定されていません。環境変数 WEATHER_LOCATIONS にカンマ区切りの都市名を設定してください。"

        weather_texts = [
            self._weather_adapter.get_weather_text(city) for city in cities
        ]
        return "\n\n".join(weather_texts)

    def _parse_weather_locations(self, weather_locations: str) -> list[str]:
        return [
            city.strip()
            for city in weather_locations.replace("\n", ",").split(",")
            if city.strip()
        ]

    def _get_single_city_weather(self, location: Optional[str]) -> str:
        city = location if location else "東京"
        return self._weather_adapter.get_weather_text(city)

    def _extract_location_from_weather_query(self, text: str) -> Optional[str]:
        match = re.search(r"(.+?)の天気", text)
        if match:
            return match.group(1).strip()
        return None
