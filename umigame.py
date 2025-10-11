import re
import logging
from openai_helpers import call_openai_yesno_with_secret, generate_umigame_puzzle

logger = logging.getLogger(__name__)

# Per-user in-memory mode state for "ウミガメのスープ"
# key: user_id -> dict {'puzzle': str, 'answer': str}
UMIGAME_STATE = {}


def is_closed_question(text: str) -> bool:
    """簡易なクローズドクエスチョン判定。

    日本語のはい/いいえで答えられる質問（疑問詞が含まれない、または yes/no 型の助動詞を末尾に持つ）を緩く判定します。
    完全な判定は困難なので非常に保守的に扱います。
    """
    t = text.strip()
    if not t:
        return False

    # common open-question keywords
    open_keywords = ['何', 'なぜ', 'どうして', 'どの', 'どこ', '誰', 'いつ', 'どれ', 'どのくらい', 'どんな', 'どれくらい', 'どうやって']
    # if any of these appear anywhere and are used as interrogatives, treat as open question
    for w in open_keywords:
        if w in t:
            return False

    # closed question indicators at the end
    closed_endings = ['か？', 'か?', 'かな?', 'かな？', 'か', '?', '？']
    if t.endswith(tuple(closed_endings)):
        return True

    # phrases that often expect yes/no answer
    yesno_patterns = [
        'できますか', 'ありますか', 'いますか', '知っていますか', '分かりますか', '〜ますか', 'でしょうか', '可能ですか', '可能でしょうか'
    ]
    for p in yesno_patterns:
        if p in t:
            return True

    # short direct questions like 'これでいい？' or 'そう？'
    if len(t) <= 20 and t.endswith(('？', '?')):
        return True

    return False


# generate_umigame_puzzle and call_openai_yesno_with_secret are provided by openai_helpers
