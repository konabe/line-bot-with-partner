from typing import Any

from src.application.usecases.send_pokemon_zukan_usecase import SendPokemonZukanUsecase
from src.domain.models.pokemon_info import PokemonInfo


def test_send_pokemon_zukan_success():
    """ポケモン情報取得成功時のテスト"""
    sent = []

    def fake_reply(req):
        sent.append(req)

    class FakeLineAdapter:
        def reply_message(self, req):
            fake_reply(req)

    class FakePokemonAdapter:
        def get_random_pokemon_info(self):
            return PokemonInfo(
                zukan_no=25,
                name="ピカチュウ",
                types=["electric"],
                image_url="https://example.com/pikachu.png",
            )

    class FakeEvent:
        def __init__(self):
            self.reply_token = "test_token"

    usecase = SendPokemonZukanUsecase(FakeLineAdapter(), FakePokemonAdapter())
    event = FakeEvent()

    usecase.execute(event)

    # メッセージが送信されることを確認
    assert len(sent) >= 1


def test_send_pokemon_zukan_failure():
    """ポケモン情報取得失敗時のテスト"""
    sent = []

    def fake_reply(req):
        sent.append(req)

    class FakeLineAdapter:
        def reply_message(self, req):
            fake_reply(req)

    class FakePokemonAdapter:
        def get_random_pokemon_info(self):
            return None  # 失敗をシミュレート

    class FakeEvent:
        def __init__(self):
            self.reply_token = "test_token"

    usecase = SendPokemonZukanUsecase(FakeLineAdapter(), FakePokemonAdapter())
    event = FakeEvent()

    usecase.execute(event)

    # エラーメッセージが送信されることを確認
    assert len(sent) == 1
    # エラーメッセージの内容を確認
    message_text = sent[0].messages[0].text
    assert "取得に失敗" in message_text
