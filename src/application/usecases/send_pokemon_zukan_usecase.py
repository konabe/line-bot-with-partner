from linebot.v3.webhooks.models.message_event import MessageEvent

from ...domain.models.pokemon_info import PokemonInfo
from ...infrastructure.line_model.zukan_button_template import (
    create_pokemon_zukan_button_template,
)
from .base_usecase import BaseUsecase
from .protocols import LineAdapterProtocol, PokemonAdapterProtocol


class SendPokemonZukanUsecase(BaseUsecase):
    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        pokemon_adapter: PokemonAdapterProtocol,
    ):
        super().__init__(line_adapter)
        self.pokemon_adapter = pokemon_adapter

    def execute(self, event: MessageEvent) -> None:
        self._logger.info("ポケモンリクエスト受信。図鑑風情報を返信")

        reply_token = event.reply_token
        if not reply_token:
            self._logger.warning("reply_tokenが存在しないため、応答をスキップします")
            return

        info = self.pokemon_adapter.get_random_pokemon_info()
        if not info:
            self._send_error_reply(
                reply_token, "ポケモン図鑑情報の取得に失敗しました。"
            )
            return

        self._send_pokemon_zukan_message(event, info)

    def _send_pokemon_zukan_message(
        self, event: MessageEvent, info: PokemonInfo
    ) -> None:
        reply_token = event.reply_token
        if not reply_token:
            return

        try:
            candidate = create_pokemon_zukan_button_template(info)
            self._send_reply(reply_token, [candidate])
        except Exception as e:
            self._logger.error(f"ポケモンメッセージ送信エラー: {e}")
            self._send_error_reply(
                reply_token, "ポケモン図鑑情報の取得に失敗しました。"
            )
