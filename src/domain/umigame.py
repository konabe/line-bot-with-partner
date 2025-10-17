import re
import logging
from ..infrastructure.openai_helpers import OpenAIClient

logger = logging.getLogger(__name__)

UMIGAME_STATE = {}

# OpenAIクライアントのインスタンス（遅延初期化）
_openai_client = None

def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient()
    return _openai_client


def is_closed_question(text: str) -> bool:
    t = text.strip()
    if not t:
        return False

    open_keywords = ['何', 'なぜ', 'どうして', 'どの', 'どこ', '誰', 'いつ', 'どれ', 'どのくらい', 'どんな', 'どれくらい', 'どうやって']
    for w in open_keywords:
        if w in t:
            return False

    closed_endings = ['か？', 'か?', 'かな?', 'かな？', 'か', '?', '？']
    if t.endswith(tuple(closed_endings)):
        return True

    yesno_patterns = [
        'できますか', 'ありますか', 'いますか', '知っていますか', '分かりますか', '〜ますか', 'でしょうか', '可能ですか', '可能でしょうか'
    ]
    for p in yesno_patterns:
        if p in t:
            return True

    if len(t) <= 20 and t.endswith(('？', '?')):
        return True

    return False
