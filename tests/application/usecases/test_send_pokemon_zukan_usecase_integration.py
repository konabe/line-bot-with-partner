from unittest.mock import MagicMock

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from src.application.usecases.send_pokemon_zukan_usecase import SendPokemonZukanUsecase
from src.domain.models.pokemon_info import PokemonInfo
from tests.support.mock_adapter import MockMessagingAdapter


class FakeEvent:
    def __init__(self):
        self.reply_token = "test_reply_token_123"


def test_execute_with_successful_pokemon_info():
    """ポケモン情報が正常に取得できる場合の結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_pokemon_adapter = MagicMock()

    pokemon_info = PokemonInfo(
        name="ピカチュウ",
        zukan_no=25,
        types=["electric"],
        image_url="https://example.com/pikachu.png",
    )
    mock_pokemon_adapter.get_random_pokemon_info.return_value = pokemon_info

    usecase = SendPokemonZukanUsecase(mock_line_adapter, mock_pokemon_adapter)
    event = FakeEvent()

    usecase.execute(event)

    mock_pokemon_adapter.get_random_pokemon_info.assert_called_once()

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert reply.reply_token == "test_reply_token_123"
    assert len(reply.messages) == 1


def test_execute_with_no_pokemon_info():
    """ポケモン情報が取得できない場合のエラーハンドリング結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_pokemon_adapter = MagicMock()
    mock_pokemon_adapter.get_random_pokemon_info.return_value = None

    usecase = SendPokemonZukanUsecase(mock_line_adapter, mock_pokemon_adapter)
    event = FakeEvent()

    usecase.execute(event)

    mock_pokemon_adapter.get_random_pokemon_info.assert_called_once()

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert reply.reply_token == "test_reply_token_123"
    assert len(reply.messages) == 1
    assert isinstance(reply.messages[0], TextMessage)
    assert "失敗" in reply.messages[0].text


def test_execute_with_pokemon_adapter_exception():
    """ポケモンアダプターで例外が発生した場合の結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_pokemon_adapter = MagicMock()
    mock_pokemon_adapter.get_random_pokemon_info.side_effect = RuntimeError("API Error")

    usecase = SendPokemonZukanUsecase(mock_line_adapter, mock_pokemon_adapter)
    event = FakeEvent()

    try:
        usecase.execute(event)
    except RuntimeError:
        pass

    mock_pokemon_adapter.get_random_pokemon_info.assert_called_once()


def test_execute_with_multiple_types_pokemon():
    """複数タイプのポケモン情報でも正常に動作する結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_pokemon_adapter = MagicMock()

    pokemon_info = PokemonInfo(
        name="リザードン",
        zukan_no=6,
        types=["fire", "flying"],
        image_url="https://example.com/charizard.png",
    )
    mock_pokemon_adapter.get_random_pokemon_info.return_value = pokemon_info

    usecase = SendPokemonZukanUsecase(mock_line_adapter, mock_pokemon_adapter)
    event = FakeEvent()

    usecase.execute(event)

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
