"""じゃんけんゲームのドメインロジック"""

import random
from typing import Dict


class JankenGame:
    """じゃんけんゲームを管理するドメインクラス"""

    # じゃんけんの手の定義
    HANDS = {
        '✊': 'グー',
        '✌️': 'チョキ',
        '✋': 'パー'
    }

    def __init__(self):
        self._hands = list(self.HANDS.keys())

    def play(self, user_hand: str) -> Dict[str, str]:
        """
        じゃんけんを実行し、結果を返す

        Args:
            user_hand: ユーザーの手（✊, ✌️, ✋）

        Returns:
            結果を含む辞書
            {
                'user_hand': '✊',
                'bot_hand': '✌️',
                'result': 'あなたの勝ち！'
            }
        """
        if user_hand not in self._hands:
            raise ValueError(f"無効な手です: {user_hand}")

        bot_hand = random.choice(self._hands)
        result = self._judge(user_hand, bot_hand)

        return {
            'user_hand': user_hand,
            'bot_hand': bot_hand,
            'result': result
        }

    def _judge(self, user: str, bot: str) -> str:
        """じゃんけんの勝敗を判定します。"""
        if user == bot:
            return 'あいこ'

        # 勝敗判定: (ユーザー, ボット) の組み合わせ
        winning_combinations = [
            ('✊', '✌️'),  # グーはチョキに勝つ
            ('✌️', '✋'),  # チョキはパーに勝つ
            ('✋', '✊')   # パーはグーに勝つ
        ]

        if (user, bot) in winning_combinations:
            return 'あなたの勝ち！'
        else:
            return 'あなたの負け…'

    def get_hand_name(self, hand: str) -> str:
        """手の絵文字から名前を取得"""
        return self.HANDS.get(hand, '不明')

    def get_available_hands(self) -> list:
        """利用可能な手の一覧を返す"""
        return self._hands.copy()