import logging
import random
from linebot.v3.messaging.models import TextMessage

logger = logging.getLogger(__name__)


def handle_postback(event, safe_reply_message, get_fallback_destination):
    """LINE からのポストバックイベントを処理します。"""
    data = event.postback.data
    logger.debug(f"handle_postback called. data: {data}")
    if data and data.startswith("janken:"):
        user_hand = data.split(":")[1]
        JANKEN_EMOJIS = {'✊': 'グー', '✌️': 'チョキ', '✋': 'パー'}
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


def judge_janken(user, bot):
    """じゃんけん（グー・チョキ・パー）の結果を判定します。"""
    if user == bot:
        return 'あいこ'
    if (user, bot) in [('✊', '✌️'), ('✌️', '✋'), ('✋', '✊')]:
        return 'あなたの勝ち！'
    else:
        return 'あなたの負け…'