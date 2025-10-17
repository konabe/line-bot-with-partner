import logging
from linebot.v3.messaging.models import TextMessage
from ..domain.janken import JankenGame

logger = logging.getLogger(__name__)


def handle_postback(event, safe_reply_message):
    """LINE からのポストバックイベントを処理します。"""
    data = event.postback.data
    logger.debug(f"handle_postback called. data: {data}")
    if data and data.startswith("janken:"):
        user_hand = data.split(":")[1]
        game = JankenGame()
        try:
            result = game.play(user_hand)
            reply = f"あなた: {result['user_hand']}\nBot: {result['bot_hand']}\n結果: {result['result']}"
            logger.info(f"じゃんけん結果: {reply}")
        except ValueError as e:
            reply = f"エラー: {e}"
            logger.error(f"じゃんけんエラー: {e}")

        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply)]
        )
        safe_reply_message(reply_message_request)