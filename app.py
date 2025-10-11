import os
import threading
import logging
import requests
from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot.v3.messaging import MessagingApi
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks.models.message_event import MessageEvent
from linebot.v3.webhooks.models.text_message_content import TextMessageContent
from linebot.v3.messaging.models import TextMessage, FlexMessage, TemplateMessage, ButtonsTemplate, PostbackAction
from linebot.v3.exceptions import InvalidSignatureError
import re
from functools import lru_cache

load_dotenv()

CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

messaging_api = MessagingApi(CHANNEL_ACCESS_TOKEN)
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


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text
    # じゃんけんテンプレート表示
    if text.strip() == 'じゃんけん':
        template = TemplateMessage(
            alt_text="じゃんけんしましょう！",
            template=ButtonsTemplate(
                title="じゃんけん",
                text="どれを出しますか？",
                actions=[
                    PostbackAction(label="✊ グー", data="janken:✊"),
                    PostbackAction(label="✌️ チョキ", data="janken:✌️"),
                    PostbackAction(label="✋ パー", data="janken:✋")
                ]
            )
        )
        messaging_api.reply_message(event.reply_token, [template])
        return
# じゃんけんのpostbackイベントハンドラ
from linebot.v3.webhooks.models.postback_event import PostbackEvent
@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data
    if data and data.startswith("janken:"):
        user_hand = data.split(":")[1]
        JANKEN_EMOJIS = {'✊': 'グー', '✌️': 'チョキ', '✋': 'パー'}
        import random
        bot_hand = random.choice(list(JANKEN_EMOJIS.keys()))
        result = judge_janken(user_hand, bot_hand)
        reply = f"あなた: {user_hand}\nBot: {bot_hand}\n結果: {result}"
        messaging_api.reply_message(event.reply_token, [TextMessage(text=reply)])
    # ポケモン名出力機能
    if text.strip() == 'ポケモン':
        info = get_random_pokemon_zukan_info()
        if info is None:
            reply = TextMessage(text="ポケモン情報の取得に失敗しました")
            messaging_api.reply_message(event.reply_token, [reply])
            return
        flex = create_pokemon_zukan_flex(info)
        messaging_api.reply_message(event.reply_token, [flex])
        return
# pokeapiから図鑑風情報を取得
def get_random_pokemon_zukan_info():
    import random
    import requests
    try:
        resp = requests.get('https://pokeapi.co/api/v2/pokemon?limit=1')
        resp.raise_for_status()
        count = resp.json().get('count', 1000)
        poke_id = random.randint(1, count)
        resp2 = requests.get(f'https://pokeapi.co/api/v2/pokemon/{poke_id}')
        resp2.raise_for_status()
        name = resp2.json().get('name', '不明')
        image_url = resp2.json().get('sprites', {}).get('other', {}).get('official-artwork', {}).get('front_default')
        types = [t['type']['name'] for t in resp2.json().get('types', [])]
        # 日本語名取得（speciesエンドポイント）
        species_url = resp2.json().get('species', {}).get('url')
        zukan_no = poke_id
        evolution = ""
        if species_url:
            resp3 = requests.get(species_url)
            resp3.raise_for_status()
            names = resp3.json().get('names', [])
            for n in names:
                if n.get('language', {}).get('name') == 'ja':
                    name = n.get('name')
                    break
            zukan_no = resp3.json().get('id', poke_id)
            # 進化情報取得
            evo_url = resp3.json().get('evolution_chain', {}).get('url')
            if evo_url:
                resp4 = requests.get(evo_url)
                resp4.raise_for_status()
                chain = resp4.json().get('chain', {})
                evo_names = []
                def extract_evo_names(chain):
                    if 'species' in chain:
                        evo_names.append(chain['species']['name'])
                    for e in chain.get('evolves_to', []):
                        extract_evo_names(e)
                extract_evo_names(chain)
                evolution = ' → '.join(evo_names)
        return {
            'zukan_no': zukan_no,
            'name': name,
            'image_url': image_url,
            'types': types,
            'evolution': evolution
        }
    except Exception:
        return None

# 図鑑風FLEX Message生成
from linebot.models import FlexSendMessage
def create_pokemon_zukan_flex(info):
    type_text = ' / '.join(info['types']) if info['types'] else '不明'
    flex = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": info['image_url'] or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png",
            "size": "xl",
            "aspectRatio": "1:1",
            "aspectMode": "cover"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"No.{info['zukan_no']} {info['name']}",
                    "weight": "bold",
                    "size": "xl",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": f"タイプ: {type_text}",
                    "size": "md",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": f"進化: {info['evolution']}",
                    "size": "sm",
                    "align": "center"
                }
            ]
        }
    }
    return FlexSendMessage(alt_text=f"ポケモン図鑑: {info['name']}", contents=flex)

    # じゃんけん絵文字判定
    JANKEN_EMOJIS = {'✊': 'グー', '✌️': 'チョキ', '✋': 'パー'}
    if text in JANKEN_EMOJIS:
        import random
        bot_hand = random.choice(list(JANKEN_EMOJIS.keys()))
        user_hand = text
        # 勝敗判定
        result = judge_janken(user_hand, bot_hand)
        reply = f"あなた: {user_hand}\nBot: {bot_hand}\n結果: {result}"
    messaging_api.reply_message(event.reply_token, [TextMessage(text=reply)])
    return

# pokeapiからランダムなポケモン名と画像URLを取得
def get_random_pokemon_info():
    import random
    import requests
    try:
        resp = requests.get('https://pokeapi.co/api/v2/pokemon?limit=1')
        resp.raise_for_status()
        count = resp.json().get('count', 1000)
        poke_id = random.randint(1, count)
        resp2 = requests.get(f'https://pokeapi.co/api/v2/pokemon/{poke_id}')
        resp2.raise_for_status()
        name = resp2.json().get('name', '不明')
        image_url = resp2.json().get('sprites', {}).get('other', {}).get('official-artwork', {}).get('front_default')
        # 日本語名取得（speciesエンドポイント）
        species_url = resp2.json().get('species', {}).get('url')
        if species_url:
            resp3 = requests.get(species_url)
            resp3.raise_for_status()
            names = resp3.json().get('names', [])
            for n in names:
                if n.get('language', {}).get('name') == 'ja':
                    name = n.get('name')
                    break
        return {'name': name, 'image_url': image_url}
    except Exception:
        return None

# FLEX Message生成
from linebot.models import FlexSendMessage
def create_pokemon_flex(name, image_url):
    flex = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": image_url or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png",
            "size": "xl",
            "aspectRatio": "1:1",
            "aspectMode": "cover"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": name,
                    "weight": "bold",
                    "size": "xl",
                    "align": "center"
                }
            ]
        }
    }
    return FlexSendMessage(alt_text=f"今日のポケモン: {name}", contents=flex)

    # ...existing code...

# じゃんけん判定関数
def judge_janken(user, bot):
    if user == bot:
        return 'あいこ'
    if (user, bot) in [('✊', '✌️'), ('✌️', '✋'), ('✋', '✊')]:
        return 'あなたの勝ち！'
    else:
        return 'あなたの負け…'


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


# ---- Generic location weather ---------------------------------------------

_WEATHER_CURRENT_FIELDS = 'temperature_2m,weather_code,wind_speed_10m'


def extract_location_from_weather_query(text: str):
    """『◯◯の天気』形式なら ◯◯ を返す。

    許容例: '東京の天気', ' 東京 の天気', '大阪の天気？', '札幌の天気です' など。
    末尾に句読点/助詞が付いても最初のマッチを利用。
    """
    # 全角スペース→半角、全角『？』など除去用に末尾記号を落とす
    t = re.sub(r'[\u3000]', ' ', text)
    m = re.search(r'(.+?)の天気', t)
    if not m:
        return None
    loc = m.group(1).strip()
    # 不要な助詞/語尾 (です/は/って) を雑に除去
    loc = re.sub(r'(?:は|って|です)$', '', loc)
    if not loc:
        return None
    return loc


@lru_cache(maxsize=128)
def geocode_location(name: str):
    """地名を Open-Meteo Geocoding で緯度経度へ解決。

    Returns: (lat, lon, resolved_name) or None
    """
    url = (
        'https://geocoding-api.open-meteo.com/v1/search'
        f'?name={requests.utils.quote(name)}&count=1&language=ja&format=json'
    )
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        results = data.get('results') or []
        if not results:
            return None
        r0 = results[0]
        return (r0.get('latitude'), r0.get('longitude'), r0.get('name'))
    except Exception:
        return None


def get_location_weather_text(location_name: str):
    geo = geocode_location(location_name)
    if not geo:
        return f"『{location_name}』の天気を見つけられませんでした"
    lat, lon, resolved = geo
    url = (
        'https://api.open-meteo.com/v1/forecast'
        f'?latitude={lat}&longitude={lon}&current={_WEATHER_CURRENT_FIELDS}'
        '&timezone=Asia%2FTokyo&language=ja'
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
        shown = resolved or location_name
        return f"{shown}の現在の天気: {desc} / 気温 {temp}℃ / 風速 {wind}m/s"
    except Exception:
        return f"現在{location_name}の天気を取得できませんでした"



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))



