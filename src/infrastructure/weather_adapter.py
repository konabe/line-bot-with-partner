import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class WeatherAdapter:
    """OpenWeatherMapを使用した天気情報取得アダプター"""

    def __init__(self):
        self.api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"

    def get_weather_text(self, location: str) -> str:
        """指定された地域の天気情報をOpenWeatherMapから取得します"""
        if not self.api_key:
            logger.error("OPENWEATHERMAP_API_KEY is not set")
            return "天気情報の取得に失敗しました。管理者にAPI設定を確認してもらってください。"
        
        try:
            params = {
                'q': f"{location},JP",  # 日本の都市として検索
                'appid': self.api_key,
                'units': 'metric',  # 摂氏温度
                'lang': 'ja'  # 日本語での天気説明
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
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
            logger.error(f"OpenWeatherMap API request failed: {e}")
            return f"{location}の天気情報の取得に失敗しました。ネットワークエラーまたはAPI制限に達した可能性があります。"
        except KeyError as e:
            logger.error(f"OpenWeatherMap API response parsing failed: {e}")
            return f"{location}の天気情報の解析に失敗しました。"
        except Exception as e:
            logger.error(f"Unexpected error in weather fetch: {e}")
            return f"{location}の天気情報の取得中に予期しないエラーが発生しました。"