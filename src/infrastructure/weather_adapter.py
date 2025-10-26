import os
import requests
from typing import Optional
from .logger import Logger, create_logger


class WeatherAdapter:
    def __init__(self, logger: Optional[Logger] = None):
        self.api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.logger: Logger = logger or create_logger(__name__)

    def get_weather_text(self, location: str) -> str:
        """指定された地域の天気情報をOpenWeatherMapから取得します"""
        if not self.api_key:
            self.logger.error("OPENWEATHERMAP_API_KEY is not set")
            return "天気情報の取得に失敗しました。管理者にAPI設定を確認してもらってください。"
        
        try:
            params = {
                'q': f"{location},JP",  # 日本の都市として検索
                'appid': self.api_key,
                'units': 'metric',  # 摂氏温度
                'lang': 'ja'  # 日本語での天気説明
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            # 404 の場合は都市が見つからないので明示的にハンドリングする
            if response.status_code == 404:
                self.logger.info(f"OpenWeatherMap: location not found: {location}")
                return f"{location}の天気情報が見つかりませんでした。地域名を確認してください。"

            response.raise_for_status()
            data = response.json()
            
            # 天気情報を抽出
            weather_desc = data['weather'][0]['description']
            temp = round(data['main']['temp'])
            feels_like = round(data['main']['feels_like'])
            humidity = data['main']['humidity']
            
            return (f"{location}の天気: {weather_desc}\n"
                    f"気温: {temp}℃ (体感 {feels_like}℃)\n"
                    f"湿度: {humidity}%")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"OpenWeatherMap API request failed: {e}")
            return f"{location}の天気情報の取得に失敗しました。ネットワークエラーまたはAPI制限に達した可能性があります。"
        except KeyError as e:
            self.logger.error(f"OpenWeatherMap API response parsing failed: {e}")
            return f"{location}の天気情報の解析に失敗しました。"
        except Exception as e:
            self.logger.error(f"Unexpected error in weather fetch: {e}")
            return f"{location}の天気情報の取得中に予期しないエラーが発生しました。"