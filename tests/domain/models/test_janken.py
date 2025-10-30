import pytest

from src.domain.models.janken import Hand, JankenBattle, JankenGame


class TestHand:
    """Handクラスのテスト"""

    def test_hand_instances_are_created(self):
        """Handクラスのインスタンスが正しく作成されている"""
        assert Hand.ROCK is not None
        assert Hand.SCISSORS is not None
        assert Hand.PAPER is not None

        assert Hand.ROCK.emoji == "✊"
        assert Hand.ROCK.name == "グー"
        assert Hand.SCISSORS.emoji == "✌️"
        assert Hand.SCISSORS.name == "チョキ"
        assert Hand.PAPER.emoji == "✋"
        assert Hand.PAPER.name == "パー"

    def test_hand_str_representation(self):
        """Handの文字列表現が絵文字を返す"""
        assert str(Hand.ROCK) == "✊"
        assert str(Hand.SCISSORS) == "✌️"
        assert str(Hand.PAPER) == "✋"

    def test_hand_equality(self):
        """Handインスタンスの等価性比較"""
        # 同じインスタンスは等しい
        rock1 = Hand.ROCK
        rock2 = Hand.ROCK
        assert rock1 == rock2
        # 異なるインスタンスは等しくない
        assert Hand.ROCK != Hand.SCISSORS
        # 異なる型のオブジェクトとは等しくない
        assert Hand.ROCK != "✊"

    def test_hand_hash(self):
        """Handインスタンスのハッシュ値"""
        # 同じ絵文字のインスタンスは同じハッシュ値
        rock1 = Hand("✊", "グー")
        rock2 = Hand("✊", "グー")
        assert hash(rock1) == hash(rock2)

    def test_get_all_hands(self):
        """get_all_hands()が全ての手を返す"""
        hands = Hand.get_all_hands()
        assert len(hands) == 3
        assert Hand.ROCK in hands
        assert Hand.SCISSORS in hands
        assert Hand.PAPER in hands

    def test_from_emoji_valid(self):
        """from_emoji()が有効な絵文字から正しいHandを返す"""
        assert Hand.from_emoji("✊") == Hand.ROCK
        assert Hand.from_emoji("✌️") == Hand.SCISSORS
        assert Hand.from_emoji("✋") == Hand.PAPER

    def test_from_emoji_invalid(self):
        """from_emoji()が無効な絵文字でValueErrorを投げる"""
        with pytest.raises(ValueError, match="無効な手です"):
            Hand.from_emoji("invalid")


class TestJankenBattle:
    """JankenBattleクラスのテスト"""

    def test_draw_result(self):
        """あいこの場合"""
        battle = JankenBattle(Hand.ROCK, Hand.ROCK)
        assert battle.get_result() == "あいこ"

    def test_user_wins(self):
        """ユーザーの勝ちの場合"""
        # グー vs チョキ → グーの勝ち
        battle = JankenBattle(Hand.ROCK, Hand.SCISSORS)
        assert battle.get_result() == "あなたの勝ち！"

        # チョキ vs パー → チョキの勝ち
        battle = JankenBattle(Hand.SCISSORS, Hand.PAPER)
        assert battle.get_result() == "あなたの勝ち！"

        # パー vs グー → パーの勝ち
        battle = JankenBattle(Hand.PAPER, Hand.ROCK)
        assert battle.get_result() == "あなたの勝ち！"

    def test_user_loses(self):
        """ユーザーの負けの場合"""
        # グー vs パー → グーの負け
        battle = JankenBattle(Hand.ROCK, Hand.PAPER)
        assert battle.get_result() == "あなたの負け…"

        # チョキ vs グー → チョキの負け
        battle = JankenBattle(Hand.SCISSORS, Hand.ROCK)
        assert battle.get_result() == "あなたの負け…"

        # パー vs チョキ → パーの負け
        battle = JankenBattle(Hand.PAPER, Hand.SCISSORS)
        assert battle.get_result() == "あなたの負け…"

    def test_to_dict(self):
        """to_dict()が正しい辞書を返す"""
        battle = JankenBattle(Hand.ROCK, Hand.SCISSORS)
        result = battle.to_dict()

        expected = {"user_hand": "✊", "bot_hand": "✌️", "result": "あなたの勝ち！"}
        assert result == expected


class TestJankenGame:
    """JankenGameクラスのテスト"""

    def test_init(self):
        """JankenGameの初期化"""
        game = JankenGame()
        hands = game.get_available_hands()
        assert len(hands) == 3
        assert Hand.ROCK in hands
        assert Hand.SCISSORS in hands
        assert Hand.PAPER in hands

    def test_play_valid_hand(self):
        """有効な手でのプレイ"""
        game = JankenGame()
        result = game.play("✊")

        assert "user_hand" in result
        assert "bot_hand" in result
        assert "result" in result

        assert result["user_hand"] == "✊"
        assert result["bot_hand"] in ["✊", "✌️", "✋"]
        assert result["result"] in ["あなたの勝ち！", "あなたの負け…", "あいこ"]

    def test_play_invalid_hand(self):
        """無効な手でのプレイでValueErrorを投げる"""
        game = JankenGame()
        with pytest.raises(ValueError, match="無効な手です"):
            game.play("invalid")

    def test_get_available_hands(self):
        """get_available_hands()が手のリストを返す"""
        game = JankenGame()
        hands = game.get_available_hands()
        assert len(hands) == 3
        assert all(isinstance(hand, Hand) for hand in hands)

    def test_get_hand_name_valid(self):
        """有効な絵文字から手名を取得"""
        game = JankenGame()
        assert game.get_hand_name("✊") == "グー"
        assert game.get_hand_name("✌️") == "チョキ"
        assert game.get_hand_name("✋") == "パー"

    def test_get_hand_name_invalid(self):
        """無効な絵文字で'不明'を返す"""
        game = JankenGame()
        assert game.get_hand_name("invalid") == "不明"
