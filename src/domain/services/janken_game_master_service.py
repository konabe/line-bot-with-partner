"""じゃんけんの結果メッセージを組み立てるドメインサービス

このサービスは、ドメインの JankenGame を利用して勝負を実行し、
ユーザー向けの返信文字列を作成して返します。
"""

from typing import Optional

from ..models.janken import JankenGame


class JankenGameMasterService:
    """じゃんけんの勝負実行と返信文の作成を行うサービス"""

    def __init__(self, game: Optional[JankenGame] = None):
        # テスト容易性のため、JankenGame を注入可能にする
        self._game: JankenGame = game or JankenGame()

    def play_and_make_reply(self, user_hand_input: str, user_label: str) -> str:
        """ユーザーの手とラベルを受け取り、返信用の文字列を返す。

        Args:
            user_hand_input: ユーザーが選択した手の絵文字（例: '✊'）
            user_label: ユーザー表示名（例: 'あなた (太郎)' や 'あなた'）

        Returns:
            生成した返信メッセージ文字列
        """
        try:
            result = self._game.play(user_hand_input)
            reply = (
                f"{user_label}: {result['user_hand']}\n"
                f"Bot: {result['bot_hand']}\n"
                f"結果: {result['result']}"
            )
        except ValueError as e:
            # 無効な手などのドメイン例外はユーザー向けのエラーメッセージに変換する
            reply = f"{user_label}: {user_hand_input}\nエラー: {e}"

        return reply
