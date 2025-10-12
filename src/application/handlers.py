import logging
import requests
import re
from functools import lru_cache
from flask import request, abort
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks.models.message_event import MessageEvent
from linebot.v3.webhooks.models.text_message_content import TextMessageContent
from linebot.v3.webhooks.models.postback_event import PostbackEvent
from linebot.v3.messaging.models import TextMessage, FlexMessage, TemplateMessage, ButtonsTemplate, PostbackAction
from linebot.v3.exceptions import InvalidSignatureError

logger = logging.getLogger(__name__)


def register_handlers(app, handler: WebhookHandler, safe_reply_message, safe_push_message):
    _ = safe_push_message  # linter対策: 未使用パラメータ警告抑制
    """Register Flask routes and LINE webhook handlers on the given app/handler.

    This function moves routing and event-handling logic out of the top-level
    app module so application layer responsibilities are separated.
    """
    # keep safe_push_message parameter for future use; reference it to avoid linter 'unused parameter'
    _unused_safe_push_message = safe_push_message

    @app.route('/debug/zukan', methods=['GET'])
    def debug_zukan():
        name = request.args.get('name', 'ピカチュウ')
        image_url = request.args.get('image_url', '')
        zukan_no = request.args.get('zukan_no', '25')
        types = request.args.get('types', 'electric').split(',') if request.args.get('types') else []
        evolution = request.args.get('evolution', 'ピチュー → ピカチュウ → ライチュウ')
        info = {
            'zukan_no': zukan_no,
            'name': name,
            'image_url': image_url,
            'types': types,
            'evolution': evolution
        }
        flex = create_pokemon_zukan_flex(info)
        try:
            return flex.to_json(), 200, {'Content-Type': 'application/json; charset=utf-8'}
        except Exception:
            return {'error': 'unable to serialize flex'}, 500


    def get_fallback_destination(event):
        """Return a destination id for push fallback: prefer userId, then groupId, then roomId."""
        try:
            src = getattr(event, 'source', None)
            if not src:
                return None
            return (
                getattr(src, 'user_id', None)
                or getattr(src, 'userId', None)
                or getattr(src, 'group_id', None)
                or getattr(src, 'groupId', None)
                or getattr(src, 'room_id', None)
                or getattr(src, 'roomId', None)
            )
        except Exception:
            return None


    @app.route('/health', methods=['GET'])
    def health():
        logger.debug("/health endpoint called")
        return 'ok', 200


    @app.route('/callback', methods=['POST'])
    def callback():
        signature = request.headers.get('X-Line-Signature', '')
        body = request.get_data(as_text=True)
        logger.debug(f"/callback called. Signature: {signature}, Body: {body}")
        try:
            handler.handle(body, signature)
            logger.debug("handler.handle succeeded")
        except InvalidSignatureError:
            logger.error("InvalidSignatureError: signature invalid")
            # 署名不正時はLINEユーザーへ障害通知（reply_token取得可能な場合のみ）
            try:
                import json
                # bodyからreply_token抽出
                data = json.loads(body)
                for ev in data.get('events', []):
                    reply_token = ev.get('replyToken')
                    if reply_token:
                        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
                        reply_message_request = ReplyMessageRequest(
                            reply_token=reply_token,
                            messages=[TextMessage(text='署名検証に失敗しました。管理者に連絡してください。')]
                        )
                        safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(ev))
            except Exception as ex:
                logger.error(f"障害通知送信失敗: {ex}")
            abort(400)
        except Exception as e:
            logger.error(f"Exception in handler.handle: {e}")
            # その他例外時も障害通知
            try:
                import json
                data = json.loads(body)
                for ev in data.get('events', []):
                    reply_token = ev.get('replyToken')
                    if reply_token:
                        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
                        reply_message_request = ReplyMessageRequest(
                            reply_token=reply_token,
                            messages=[TextMessage(text='現在障害が発生しています。管理者に連絡してください。')]
                        )
                        safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(ev))
            except Exception as ex:
                logger.error(f"障害通知送信失敗: {ex}")
            abort(500)
        return 'OK', 200


    def handle_message(event):
        # import domain and helpers lazily to avoid circular imports at module import time
        from src.domain import UMIGAME_STATE, is_closed_question, generate_umigame_puzzle
        text = event.message.text
        logger.debug(f"handle_message called. text: {text}")
        try:
            user_id = getattr(event.source, 'user_id', None) or getattr(event.source, 'userId', None)
        except Exception:
            user_id = None

        if text.strip() == 'ウミガメのスープ':
            if user_id:
                try:
                    puzzle_obj = generate_umigame_puzzle()
                    UMIGAME_STATE[user_id] = {'puzzle': puzzle_obj.get('puzzle', ''), 'answer': puzzle_obj.get('answer', '')}
                    puzzle_text = UMIGAME_STATE[user_id]['puzzle']
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
            return

        if text.strip() == 'ウミガメのスープ終了':
            if user_id and UMIGAME_STATE.get(user_id):
                UMIGAME_STATE.pop(user_id, None)
            from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
            reply_message_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text='ウミガメのスープモードを終了しました。')]
            )
            safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(event))
            return

        if user_id and UMIGAME_STATE.get(user_id):
            if not is_closed_question(text):
                logger.info('非クローズドクエスチョンをウミガメのスープモードで無視')
                return
            try:
                secret = UMIGAME_STATE[user_id].get('answer', '')
                # delegate to domain service
                from src.domain.services.openai_helpers import call_openai_yesno_with_secret
                answer = call_openai_yesno_with_secret(text, secret)
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
                UMIGAME_STATE.pop(user_id, None)
                try:
                    reply_message_request = ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text='おめでとうございます。核心に迫る質問が来たためウミガメのスープモードを終了します。')]
                    )
                    safe_reply_message(reply_message_request)
                except Exception:
                    pass
            return

        if text.strip() == '直接送信テスト':
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
            safe_push_message(push_message_request)
            try:
                from linebot.v3.messaging.models import ReplyMessageRequest
                reply_message_request = ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="直接送信を行いました。")]
                )
                safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(event))
            except Exception:
                pass
            return

        if '天気' in text:
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
            return

        if text.strip() == 'じゃんけん':
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
            return

        if text.strip() == '今日のご飯':
            logger.info("今日のご飯リクエストを受信: ChatGPT に問い合わせます")
            try:
                suggestion = get_chatgpt_meal_suggestion()
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
            return

        if text.strip() == 'ポケモン':
            logger.info("ポケモンリクエスト受信。図鑑風情報を返信")
            info = get_random_pokemon_zukan_info()
            if info:
                flex = create_pokemon_zukan_flex(info)
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
            return


    def handle_postback(event):
        data = event.postback.data
        logger.debug(f"handle_postback called. data: {data}")
        if data and data.startswith("janken:"):
            user_hand = data.split(":")[1]
            JANKEN_EMOJIS = {'✊': 'グー', '✌️': 'チョキ', '✋': 'パー'}
            import random
            bot_hand = random.choice(list(JANKEN_EMOJIS.keys()))
            result = judge_janken(user_hand, bot_hand)
            reply = f"あなた: {user_hand}\nBot: {bot_hand}\n結果: {result}"
            logger.info(f"じゃんけん結果: {reply}")
            from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
            reply_message_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
            safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(event))


    # attach handlers to the provided WebhookHandler
    handler.add(MessageEvent, message=TextMessageContent)(handle_message)
    handler.add(PostbackEvent)(handle_postback)


    # ---------------- helper functions moved from app.py -----------------
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
                resp3 = requests.get(species_url)
                resp3.raise_for_status()
                names = resp3.json().get('names', [])
                for n in names:
                    if n.get('language', {}).get('name') == 'ja':
                        name = n.get('name')
                        break
                zukan_no = resp3.json().get('id', poke_id)
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


    def create_pokemon_zukan_flex(info):
        from linebot.v3.messaging.models import FlexBubble, FlexImage, FlexBox, FlexText, FlexSeparator
        types = info.get('types') or []
        zukan_no = info.get('zukan_no') or ''
        name = info.get('name') or '不明'
        evolution = info.get('evolution') or 'なし'
        hero = FlexImage(
            url=info['image_url'] or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png",
            size="xl",
            aspect_ratio="1:1",
            aspect_mode="cover"
        )
        try:
            z_no = int(zukan_no)
            zukan_display = f"No.{z_no:03d}"
        except Exception:
            zukan_display = f"No.{zukan_no}"
        header = FlexBox(
            layout="vertical",
            contents=[
                FlexText(text=zukan_display, weight="bold", size="sm", color="#999999", align="center"),
                FlexText(text=name, weight="bold", size="xl", align="center")
            ]
        )
        type_items = []
        for t in types:
            color = "#666666"
            try:
                h = abs(hash(t))
                palette = ["#A8A77A", "#C22E28", "#A33EA1", "#E2BF65", "#7AC74C", "#B7B7CE", "#6390F0"]
                color = palette[h % len(palette)]
            except Exception:
                color = "#666666"
            type_items.append(FlexText(text=t, size="sm", color=color, align="center"))
        types_box = FlexBox(layout="baseline", contents=type_items)
        evo = FlexText(text=f"進化: {evolution}", size="sm", color="#666666", align="center")
        footer = FlexBox(layout="vertical", contents=[
            types_box,
            FlexSeparator(margin="sm"),
            evo
        ])
        body = FlexBox(layout="vertical", contents=[
            header,
            FlexSeparator(margin="md")
        ])
        bubble = FlexBubble(hero=hero, body=body, footer=footer)
        return FlexMessage(alt_text=f"ポケモン図鑑: {name}", contents=bubble)


    def get_random_pokemon_info():
        import random
        try:
            logger.debug("get_random_pokemon_info called")
            resp = requests.get('https://pokeapi.co/api/v2/pokemon?limit=1')
            resp.raise_for_status()
            count = resp.json().get('count', 1000)
            poke_id = random.randint(1, count)
            resp2 = requests.get(f'https://pokeapi.co/api/v2/pokemon/{poke_id}')
            resp2.raise_for_status()
            name = resp2.json().get('name', '不明')
            image_url = resp2.json().get('sprites', {}).get('other', {}).get('official-artwork', {}).get('front_default')
            species_url = resp2.json().get('species', {}).get('url')
            if species_url:
                resp3 = requests.get(species_url)
                resp3.raise_for_status()
                names = resp3.json().get('names', [])
                for n in names:
                    if n.get('language', {}).get('name') == 'ja':
                        name = n.get('name')
                        break
            logger.info(f"取得したポケモン: {name}")
            return {'name': name, 'image_url': image_url}
        except Exception as e:
            logger.error(f"get_random_pokemon_info error: {e}")
            return None


    def get_chatgpt_meal_suggestion():
        from src.domain.services.openai_helpers import get_chatgpt_meal_suggestion as svc
        return svc()


    def create_pokemon_flex(name, image_url):
        from linebot.v3.messaging.models import FlexBubble, FlexImage, FlexBox, FlexText
        hero = FlexImage(url=image_url or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png", size="xl", aspect_ratio="1:1", aspect_mode="cover")
        body = FlexBox(layout="vertical", contents=[
            FlexText(text=name, weight="bold", size="xl", align="center")
        ])
        bubble = FlexBubble(hero=hero, body=body)
        return FlexMessage(alt_text=f"今日のポケモン: {name}", contents=bubble)


    def judge_janken(user, bot):
        if user == bot:
            return 'あいこ'
        if (user, bot) in [('✊', '✌️'), ('✌️', '✋'), ('✋', '✊')]:
            return 'あなたの勝ち！'
        else:
            return 'あなたの負け…'


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
