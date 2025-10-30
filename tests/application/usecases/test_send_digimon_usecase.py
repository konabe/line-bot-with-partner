"""SendDigimonUsecase のテスト"""

from src.application.usecases.send_digimon_usecase import SendDigimonUsecase
from src.domain.models.digimon_info import DigimonInfo


class FakeLineAdapter:
    def __init__(self):
        self.reply_message_calls = []

    def reply_message(self, req):
        self.reply_message_calls.append(req)

    def push_message(self, req):
        pass

    def get_display_name_from_line_profile(self, user_id: str) -> str:
        return "TestUser"


class FakeDigimonAdapter:
    def __init__(self, digimon_info=None):
        self.digimon_info = digimon_info
        self.get_random_digimon_info_calls = []

    def get_random_digimon_info(self):
        self.get_random_digimon_info_calls.append(True)
        return self.digimon_info


def _make_message_event(text: str = "デジモン", user_id: str = "U123"):
    class FakeMessage:
        def __init__(self, text: str):
            self.text = text
            self.type = "text"

    class FakeSource:
        def __init__(self, user_id: str):
            self.user_id = user_id

    class FakeEvent:
        def __init__(self, text: str, user_id: str):
            self.message = FakeMessage(text)
            self.source = FakeSource(user_id)
            self.reply_token = "fake_reply_token"

    return FakeEvent(text, user_id)


class TestSendDigimonUsecase:
    def test_execute_success(self):
        """デジモン情報を取得してButtonTemplateメッセージを送信できること"""
        line_adapter = FakeLineAdapter()
        digimon_info = DigimonInfo(
            id=1,
            name="Agumon",
            level="Rookie",
            image_url="https://example.com/agumon.png",
        )
        digimon_adapter = FakeDigimonAdapter(digimon_info)

        usecase = SendDigimonUsecase(line_adapter, digimon_adapter)
        event = _make_message_event()

        usecase.execute(event)

        assert len(digimon_adapter.get_random_digimon_info_calls) == 1
        assert len(line_adapter.reply_message_calls) == 1

        req = line_adapter.reply_message_calls[0]
        assert req.reply_token == "fake_reply_token"
        assert len(req.messages) == 1

        # TemplateMessageが送信されていることを確認
        message = req.messages[0]
        assert message.__class__.__name__ == "TemplateMessage"

    def test_execute_with_none_digimon_info(self):
        """デジモン情報がNoneの場合にエラーメッセージを送信すること"""
        line_adapter = FakeLineAdapter()
        digimon_adapter = FakeDigimonAdapter(None)

        usecase = SendDigimonUsecase(line_adapter, digimon_adapter)
        event = _make_message_event()

        usecase.execute(event)

        assert len(digimon_adapter.get_random_digimon_info_calls) == 1
        assert len(line_adapter.reply_message_calls) == 1

        req = line_adapter.reply_message_calls[0]
        assert req.messages[0].text == "デジモン図鑑情報の取得に失敗しました。"

    def test_execute_without_image_url(self):
        """image_urlがNoneでも正常に動作すること"""
        line_adapter = FakeLineAdapter()
        digimon_info = DigimonInfo(id=2, name="Gabumon", level="Rookie", image_url=None)
        digimon_adapter = FakeDigimonAdapter(digimon_info)

        usecase = SendDigimonUsecase(line_adapter, digimon_adapter)
        event = _make_message_event()

        usecase.execute(event)

        assert len(line_adapter.reply_message_calls) == 1

        # TemplateMessageが送信されていることを確認
        message = line_adapter.reply_message_calls[0].messages[0]
        assert message.__class__.__name__ == "TemplateMessage"
