"""じゃんけんゲームのドメインロジック"""

import random
from typing import Dict, List


class Hand:
    """じゃんけんの手を表すクラス"""

    # じゃんけんの手の定義
    ROCK = None  # 前方参照のため後で設定
    SCISSORS = None
    PAPER = None

    def __init__(self, emoji: str, name: str):
        self.emoji = emoji
        self.name = name

    def __str__(self):
        return self.emoji

    def __repr__(self):
        return f"Hand({self.emoji}, {self.name})"

    def __eq__(self, other):
        return isinstance(other, Hand) and self.emoji == other.emoji

    def __hash__(self):
        return hash(self.emoji)

    @classmethod
    def get_all_hands(cls) -> List['Hand']:
        """全ての手を取得"""
        return [cls.ROCK, cls.SCISSORS, cls.PAPER]

    @classmethod
    def from_emoji(cls, emoji: str) -> 'Hand':
        """絵文字からHandインスタンスを取得"""
        for hand in cls.get_all_hands():
            if hand.emoji == emoji:
                return hand
        raise ValueError(f"無効な手です: {emoji}")


# インスタンスの作成（前方参照を避けるため）
Hand.ROCK = Hand('✊', 'グー')
Hand.SCISSORS = Hand('✌️', 'チョキ')
Hand.PAPER = Hand('✋', 'パー')


class JankenBattle:
    """じゃんけんの勝負を表すクラス"""

    # 勝敗判定: (ユーザー, ボット) の組み合わせ
    WINNING_COMBINATIONS = [
        (Hand.ROCK, Hand.SCISSORS),     # グーはチョキに勝つ
        (Hand.SCISSORS, Hand.PAPER),    # チョキはパーに勝つ
        (Hand.PAPER, Hand.ROCK)         # パーはグーに勝つ
    ]

    def __init__(self, user_hand: Hand, bot_hand: Hand):
        self.user_hand = user_hand
        self.bot_hand = bot_hand

    def get_result(self) -> str:
        """勝敗結果を取得"""
        if self.user_hand == self.bot_hand:
            return 'あいこ'

        if (self.user_hand, self.bot_hand) in self.WINNING_COMBINATIONS:
            return 'あなたの勝ち！'
        else:
            return 'あなたの負け…'

    def to_dict(self) -> Dict[str, str]:
        """結果を辞書形式で返す"""
        return {
            'user_hand': self.user_hand.emoji,
            'bot_hand': self.bot_hand.emoji,
            'result': self.get_result()
        }


class JankenGame:
    """じゃんけんゲームを管理するドメインクラス"""

    def __init__(self):
        self._hands = Hand.get_all_hands()

    def play(self, user_hand_emoji: str) -> Dict[str, str]:
        """
        じゃんけんを実行し、結果を返す

        Args:
            user_hand_emoji: ユーザーの手（✊, ✌️, ✋）

        Returns:
            結果を含む辞書
            {
                'user_hand': '✊',
                'bot_hand': '✌️',
                'result': 'あなたの勝ち！'
            }
        """
        try:
            user_hand = Hand.from_emoji(user_hand_emoji)
        except ValueError:
            raise ValueError(f"無効な手です: {user_hand_emoji}")

        bot_hand = random.choice(self._hands)
        battle = JankenBattle(user_hand, bot_hand)

        return battle.to_dict()

    def get_available_hands(self) -> List[Hand]:
        """利用可能な手の一覧を返す"""
        return self._hands.copy()

    def get_hand_name(self, hand_emoji: str) -> str:
        """手の絵文字から名前を取得"""
        try:
            hand = Hand.from_emoji(hand_emoji)
            return hand.name
        except ValueError:
            return '不明'