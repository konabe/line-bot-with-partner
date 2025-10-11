import os
import requests
from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

load_dotenv()

CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')

app = Flask(__name__)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.route('/health', methods=['GET'])
def health():
    return 'ok', 200


@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK', 200


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    # キーワード: 博多の天気 (ゆるいマッチ: 空白差異/末尾句読点などを考慮)
    normalized = text.strip().replace('　', ' ')
    if '博多' in normalized and '天気' in normalized:
        weather_text = get_hakata_weather_text()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=weather_text))
        return

    # fallback echo
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))


def get_hakata_weather_text():
    """博多(福岡市付近)の現在の天気を Open-Meteo API から取得して整形した文字列を返す。

    Open-Meteo は API Key 不要・無料。レート制限緩めだが失敗時はメッセージを返す。
    緯度経度: 福岡市(博多駅付近) 33.5902, 130.4017 付近。
    """
    lat = 33.5902
    lon = 130.4017
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m"
        "&timezone=Asia%2FTokyo"
        "&language=ja"
    )
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        current = data.get('current', {})
        temp = current.get('temperature_2m')
        wind = current.get('wind_speed_10m')
        code = current.get('weather_code')
        desc = weather_code_to_japanese(code)
        if temp is None:
            raise ValueError('no temperature')
        return f"博多の現在の天気: {desc} / 気温 {temp}℃ / 風速 {wind}m/s"
    except Exception:
        return "現在天気を取得できませんでした (しばらくして再度お試しください)"


def weather_code_to_japanese(code):
    mapping = {
        0: '快晴',
        1: 'ほぼ快晴', 2: '一部曇り', 3: '曇り',
        45: '霧', 48: '霧 (霧氷)',
        51: '霧雨(弱)', 53: '霧雨(中)', 55: '霧雨(強)',
        56: '着氷性霧雨(弱)', 57: '着氷性霧雨(強)',
        61: '雨(弱)', 63: '雨(中)', 65: '雨(強)',
        66: '着氷性の雨(弱)', 67: '着氷性の雨(強)',
        71: '雪(弱)', 73: '雪(中)', 75: '雪(強)',
        77: '雪あられ',
        80: 'にわか雨(弱)', 81: 'にわか雨(中)', 82: 'にわか雨(強)',
        85: 'にわか雪(弱)', 86: 'にわか雪(強)',
        95: '雷雨', 96: '雷雨(ひょう小)', 99: '雷雨(ひょう大)',
    }
    return mapping.get(code, '不明')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
