import os
import threading
import logging
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    # 起動後に一度だけ通知するスレッドを準備
    def startup_notify_once():
        try:
            maybe_notify_startup()
        except Exception as e:
            logger.warning("startup notify failed: %s", e)

    threading.Thread(target=startup_notify_once, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))


# ---- Startup Notification -------------------------------------------------
_startup_notified = False


def maybe_notify_startup():
    """環境変数で有効化されている場合に LINE へ起動通知を一度だけ送る。

    環境変数:
      STARTUP_NOTIFY_ENABLED: '1' で有効 (デフォルト無効)
      STARTUP_NOTIFY_USER_ID: push 先の UserID (必須: 有効化時)
      STARTUP_NOTIFY_MESSAGE: 送信文 (省略時デフォルト)
    """
    global _startup_notified
    if _startup_notified:
        return
    if os.environ.get('STARTUP_NOTIFY_ENABLED') != '1':
        return
    user_id = os.environ.get('STARTUP_NOTIFY_USER_ID')
    if not user_id:
        logger.warning('STARTUP_NOTIFY_ENABLED=1 ですが STARTUP_NOTIFY_USER_ID が未設定のため送信しません')
        return
    message = os.environ.get('STARTUP_NOTIFY_MESSAGE', 'サーバーが起動しました ✅')
    try:
        line_bot_api.push_message(user_id, TextSendMessage(text=message))
        logger.info('Startup notify sent to %s', user_id)
        _startup_notified = True
    except Exception as e:
        logger.warning('起動通知送信に失敗: %s', e)

