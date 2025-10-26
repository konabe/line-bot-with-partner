from typing import Protocol, Optional


class _Postback(Protocol):
    data: Optional[str]


class _Source(Protocol):
    userId: Optional[str]


"""LINE のポストバックイベントの型を表すプロトコルクラス"""
class PostbackEventLike(Protocol):
    postback: _Postback
    reply_token: str
    source: _Source


__all__ = ["PostbackEventLike"]
