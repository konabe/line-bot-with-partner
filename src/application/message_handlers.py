import logging
import requests
import re
from functools import lru_cache
from linebot.v3.messaging.models import TextMessage, FlexMessage, TemplateMessage, ButtonsTemplate, PostbackAction
from typing import Protocol, Dict, Any, Callable
from src.infrastructure.line_model import create_pokemon_zukan_flex_dict

logger = logging.getLogger(__name__)


class DomainServices(Protocol):
    """Domain層サービスのインターフェース"""
    UMIGAME_STATE: Dict[str, Any]
    is_closed_question: Callable[[str], bool]
    generate_umigame_puzzle: Callable[[], Dict[str, str]]
    call_openai_yesno_with_secret: Callable[[str, str], str]
    get_chatgpt_meal_suggestion: Callable[[], str]
    get_chatgpt_response: Callable[[str], str]


def get_default_domain_services() -> DomainServices:
    """デフォルトのdomainサービスを取得（後方互換性のため）"""
    from src.domain import UMIGAME_STATE, is_closed_question, generate_umigame_puzzle
    from src.domain.services.openai_helpers import call_openai_yesno_with_secret, get_chatgpt_meal_suggestion, get_chatgpt_response

    class DefaultDomainServices:
        def __init__(self):
            self.UMIGAME_STATE = UMIGAME_STATE
            self.is_closed_question = is_closed_question
            self.generate_umigame_puzzle = generate_umigame_puzzle
            self.call_openai_yesno_with_secret = call_openai_yesno_with_secret
            self.get_chatgpt_meal_suggestion = get_chatgpt_meal_suggestion
            self.get_chatgpt_response = get_chatgpt_response

    return DefaultDomainServices()


def handle_umigame_start(event, safe_reply_message, get_fallback_destination, user_id, domain_services):
    if user_id:
        try:
            puzzle_obj = domain_services.generate_umigame_puzzle()
            domain_services.UMIGAME_STATE[user_id] = {'puzzle': puzzle_obj.get('puzzle', ''), 'answer': puzzle_obj.get('answer', '')}
            puzzle_text = domain_services.UMIGAME_STATE[user_id]['puzzle']
        except Exception as e:
            logger.error(f"failed to generate umigame puzzle: {e}")
            puzzle_text = '申し訳ないです。出題の生成に失敗しました。管理者に OPENAI_API_KEY の設定を確認してください。'
    else:
        puzzle_text = 'ウミガメのスープモードに入りました（ただし user_id が特定できないため内部状態は保持されません）。'
    from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
    reply_message_request = ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[TextMessage(text=(
            f"ウミガメのスープモードに入りました。出題:\n{puzzle_text}\n\n"
            "クローズドクエスチョン（はい/いいえで答えられる質問）だけ受け付けます。"
            " 終了: 「ウミガメのスープ終了」"
        ))]
    )
    safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(event))


def handle_umigame_end(event, safe_reply_message, get_fallback_destination, user_id, domain_services):
    if user_id and domain_services.UMIGAME_STATE.get(user_id):
        domain_services.UMIGAME_STATE.pop(user_id, None)
    from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
    reply_message_request = ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[TextMessage(text='ウミガメのスープモードを終了しました。')]
    )
    safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(event))


def handle_umigame_question(event, safe_reply_message, get_fallback_destination, user_id, text, domain_services):
    try:
        secret = domain_services.UMIGAME_STATE[user_id].get('answer', '')
        answer = domain_services.call_openai_yesno_with_secret(text, secret)
    except Exception as e:
        logger.error(f"call_openai_yesno failed: {e}")
        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text='申し訳ないです。OpenAI の呼び出しに失敗しました。管理者に OPENAI_API_KEY の設定を確認してください。')]
        )
        safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(event))
        return
    cleared = False
    if answer.startswith('はい') or answer.startswith('はい、'):
        cleared = True
    from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
    reply_message_request = ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[TextMessage(text=answer)]
    )
    safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(event))
    if cleared and user_id:
        domain_services.UMIGAME_STATE.pop(user_id, None)
        try:
            reply_message_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text='おめでとうございます。核心に迫る質問が来たためウミガメのスープモードを終了します。')]
            )
            safe_reply_message(reply_message_request)
        except Exception:
            pass


def handle_direct_send_test(event, safe_reply_message, get_fallback_destination):
    logger.info("直接送信テストを受信: 対象ユーザーへ push 送信を試みます")
    user_id = None
    try:
        user_id = getattr(event.source, 'user_id', None) or getattr(event.source, 'userId', None)
    except Exception:
        user_id = None
    if not user_id:
        logger.error("user_id が取得できません。push を送信できません")
        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="直接送信ができませんでした: user_id が不明です")]
        )
        safe_reply_message(reply_message_request)
        return
    try:
        from datetime import datetime
        try:
            from zoneinfo import ZoneInfo
            now = datetime.now(ZoneInfo('Asia/Tokyo'))
        except Exception:
            now = datetime.now()
        now_str = now.strftime('%Y-%m-%d %H:%M:%S %Z')
    except Exception as e:
        logger.error(f"日時文字列作成に失敗: {e}")
        now_str = '取得できませんでした'
    from linebot.v3.messaging.models import PushMessageRequest, TextMessage
    push_message_request = PushMessageRequest(
        to=user_id,
        messages=[TextMessage(text=f"現在の日時: {now_str}")]
    )
    safe_reply_message(push_message_request)  # Note: This should be safe_push_message
    try:
        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="直接送信を行いました。")]
        )
        safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(event))
    except Exception:
        pass


def handle_weather(event, safe_reply_message, get_fallback_destination, text):
    logger.info("天気リクエスト検出")
    loc = extract_location_from_weather_query(text)
    if loc:
        logger.debug(f"位置解決: {loc}")
        reply_text = get_location_weather_text(loc)
    else:
        logger.debug("位置未指定のため博多天気を返す")
        reply_text = get_hakata_weather_text()
    from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
    reply_message_request = ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[TextMessage(text=reply_text)]
    )
    safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(event))


def handle_janken(event, safe_reply_message, get_fallback_destination):
    logger.info("じゃんけんテンプレートを送信")
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
    from linebot.v3.messaging.models import ReplyMessageRequest
    reply_message_request = ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[template]
    )
    safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(event))


def handle_meal(event, safe_reply_message, get_fallback_destination, domain_services):
    logger.info("今日のご飯リクエストを受信: ChatGPT に問い合わせます")
    try:
        suggestion = domain_services.get_chatgpt_meal_suggestion()
    except Exception as e:
        logger.error(f"get_chatgpt_meal_suggestion error: {e}")
        suggestion = None
    from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
    if not suggestion:
        msg = (
            "申し訳ないです。おすすめを取得できませんでした。"
            " 管理者に OPENAI_API_KEY の設定を確認してもらってください。"
        )
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=msg)]
        )
    else:
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=suggestion)]
        )
    safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(event))


def handle_pokemon(event, safe_reply_message, get_fallback_destination):
    logger.info("ポケモンリクエスト受信。図鑑風情報を返信")
    info = get_random_pokemon_zukan_info()
    if info:
        flex = create_pokemon_zukan_flex_dict(info)
        from linebot.v3.messaging.models import ReplyMessageRequest
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[flex]
        )
        safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(event))
    else:
        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="ポケモン図鑑情報の取得に失敗しました。")]
        )
        safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(event))


def handle_chatgpt(event, safe_reply_message, get_fallback_destination, text, domain_services):
    logger.info("コマンド以外のメッセージを受信: ChatGPT に問い合わせます")
    try:
        response = domain_services.get_chatgpt_response(text)
    except Exception as e:
        logger.error(f"get_chatgpt_response error: {e}")
        response = None
    from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
    if not response:
        msg = (
            "申し訳ないです。応答を生成できませんでした。"
            "管理者に OPENAI_API_KEY の設定を確認してもらってください。"
        )
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=msg)]
        )
    else:
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=response)]
        )
    safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(event))


def handle_message(event, safe_reply_message, get_fallback_destination, domain_services=None):
    """LINE からのテキストメッセージイベントを処理します。"""
    if domain_services is None:
        domain_services = get_default_domain_services()

    text = event.message.text
    logger.debug(f"handle_message called. text: {text}")
    try:
        user_id = getattr(event.source, 'user_id', None) or getattr(event.source, 'userId', None)
    except Exception:
        user_id = None

    t = text.strip()
    if t == 'ウミガメのスープ':
        return handle_umigame_start(event, safe_reply_message, get_fallback_destination, user_id, domain_services)
    if t == 'ウミガメのスープ終了':
        return handle_umigame_end(event, safe_reply_message, get_fallback_destination, user_id, domain_services)
    if user_id and domain_services.UMIGAME_STATE.get(user_id):
        if not domain_services.is_closed_question(text):
            logger.info('非クローズドクエスチョンをウミガメのスープモードで無視')
            return
        return handle_umigame_question(event, safe_reply_message, get_fallback_destination, user_id, text, domain_services)
    if t == '直接送信テスト':
        return handle_direct_send_test(event, safe_reply_message, get_fallback_destination)
    if '天気' in text:
        return handle_weather(event, safe_reply_message, get_fallback_destination, text)
    if t == 'じゃんけん':
        return handle_janken(event, safe_reply_message, get_fallback_destination)
    if t == '今日のご飯':
        return handle_meal(event, safe_reply_message, get_fallback_destination, domain_services)
    if t == 'ポケモン':
        return handle_pokemon(event, safe_reply_message, get_fallback_destination)
    return handle_chatgpt(event, safe_reply_message, get_fallback_destination, text, domain_services)


def get_random_pokemon_zukan_info():
    import random
    try:
        logger.debug("get_random_pokemon_zukan_info called")
        resp = requests.get('https://pokeapi.co/api/v2/pokemon?limit=1')
        resp.raise_for_status()
        count = resp.json().get('count', 1000)
        poke_id = random.randint(1, min(count, 1017))
        resp2 = requests.get(f'https://pokeapi.co/api/v2/pokemon/{poke_id}')
        resp2.raise_for_status()
        name = resp2.json().get('name', '不明')
        image_url = resp2.json().get('sprites', {}).get('other', {}).get('official-artwork', {}).get('front_default')
        types = [t['type']['name'] for t in resp2.json().get('types', [])]
        species_url = resp2.json().get('species', {}).get('url')
        zukan_no = poke_id
        evolution = ""
        if species_url:
            # delegate species and evolution parsing to helper
            name, zukan_no, evolution = _parse_species_and_evolution(species_url, name, poke_id)
        logger.info(f"取得したポケモン: {name} (No.{zukan_no})")
        return {
            'zukan_no': zukan_no,
            'name': name,
            'image_url': image_url,
            'types': types,
            'evolution': evolution
        }
    except Exception as e:
        logger.error(f"get_random_pokemon_zukan_info error: {e}")
        return None


def get_chatgpt_meal_suggestion():
    from src.domain.services.openai_helpers import get_chatgpt_meal_suggestion as svc
    return svc()


def get_chatgpt_response(user_message: str):
    """ユーザーのメッセージに対してChatGPTを使って返答を生成します。"""
    from src.domain.services.openai_helpers import get_chatgpt_response as svc
    return svc(user_message)


def get_hakata_weather_text():
    lat = 33.5902
    lon = 130.4017
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m"
        "&timezone=Asia%2FTokyo"
        "&language=ja"
    )
    try:
        logger.debug(f"get_hakata_weather_text called. url: {url}")
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
        logger.info(f"博多天気: {desc}, 気温: {temp}, 風速: {wind}")
        return f"博多の現在の天気: {desc} / 気温 {temp}℃ / 風速 {wind}m/s"
    except Exception as e:
        logger.error(f"get_hakata_weather_text error: {e}")
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


_WEATHER_CURRENT_FIELDS = 'temperature_2m,weather_code,wind_speed_10m'


def extract_location_from_weather_query(text: str):
    t = text.replace('　', ' ')
    m = re.search(r'(.+?)の天気', t)
    if not m:
        return None
    loc = m.group(1).strip()
    loc = re.sub(r'(?:は|って|です)$', '', loc)
    if not loc:
        return None
    return loc


@lru_cache(maxsize=128)
def geocode_location(name: str):
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
    logger.debug(f"get_location_weather_text called. location_name: {location_name}")
    geo = geocode_location(location_name)
    if not geo:
        logger.warning(f"地名解決失敗: {location_name}")
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
        logger.info(f"{shown}の天気: {desc}, 気温: {temp}, 風速: {wind}")
        return f"{shown}の現在の天気: {desc} / 気温 {temp}℃ / 風速 {wind}m/s"
    except Exception as e:
        logger.error(f"get_location_weather_text error: {e}")
        return f"現在{location_name}の天気を取得できませんでした"


def _parse_species_and_evolution(species_url: str, default_name: str, default_id: int):
    """species API を叩いて和名と図鑑番号、進化連鎖を抽出します。"""
    try:
        resp3 = requests.get(species_url)
        resp3.raise_for_status()
        data = resp3.json()
        name = default_name
        names = data.get('names', [])
        for n in names:
            if n.get('language', {}).get('name') == 'ja':
                name = n.get('name')
                break
        zukan_no = data.get('id', default_id)
        evo_url = data.get('evolution_chain', {}).get('url')
        evolution = ''
        if evo_url:
            resp4 = requests.get(evo_url)
            resp4.raise_for_status()
            chain = resp4.json().get('chain', {})
            evo_names = []
            def extract_evo_names(chain_node):
                if 'species' in chain_node:
                    evo_names.append(chain_node['species']['name'])
                for e in chain_node.get('evolves_to', []):
                    extract_evo_names(e)
            extract_evo_names(chain)
            evolution = ' → '.join(evo_names)
        return name, zukan_no, evolution
    except Exception:
        return default_name, default_id, ''