from typing import Protocol, Optional


class _Postback(Protocol):
    data: Optional[str]


class _Source(Protocol):
    # LINE SDKs may expose either `user_id` or `userId` depending on naming conventions
    user_id: Optional[str]
    userId: Optional[str]


"""LINE のポストバックイベントの型を表すプロトコルクラス"""
class PostbackEventLike(Protocol):
    postback: _Postback
    reply_token: str
    source: _Source


__all__ = ["PostbackEventLike"]
