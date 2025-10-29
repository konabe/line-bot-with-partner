from typing import Optional, Protocol


class _Postback(Protocol):
    data: Optional[str]


class _Source(Protocol):
    user_id: Optional[str]


"""LINE のポストバックイベントの型を表すプロトコルクラス"""


class PostbackEventLike(Protocol):
    postback: _Postback
    reply_token: str
    source: _Source


__all__ = ["PostbackEventLike"]
