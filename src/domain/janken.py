"""互換性のための shim: `janken` モジュールは `domain.models.janken` に移動しました。

古いインポート (`from src.domain.janken import JankenGame`) を使っているコードとの互換性を保つため、
ここでは新しい場所からエクスポートを再公開しています。
"""

from .models.janken import *  # noqa: F401,F403

__all__ = [
    "Hand",
    "JankenBattle",
    "JankenGame",
]