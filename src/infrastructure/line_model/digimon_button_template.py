from typing import Mapping, Union

from linebot.v3.messaging.models import ButtonsTemplate, TemplateMessage, URIAction

from src.domain.models.digimon_info import DigimonInfo


def create_digimon_zukan_button_template(info: Union[DigimonInfo, Mapping]):
    if not isinstance(info, DigimonInfo):
        info = DigimonInfo.from_mapping(dict(info or {}))

    image_url = info.image_url or "https://digi-api.com/images/digimon/w/Agumon.png"
    digimon_id = info.id or 0

    try:
        digimon_id_str = f"{int(digimon_id):04d}"
    except Exception:
        digimon_id_str = str(digimon_id)

    title = f"No.{digimon_id_str} {info.name or ''}".strip()

    detail_url = f"https://digi-api.com/digimon/{digimon_id}"

    actions = [URIAction(label="図鑑で見る", uri=detail_url, altUri=None)]

    template = ButtonsTemplate(
        title=title,
        text=f"レベル: {info.level or '不明'}",
        thumbnailImageUrl=image_url,
        actions=actions,
        imageAspectRatio="rectangle",
        imageSize="cover",
        imageBackgroundColor="#FFFFFF",
        defaultAction=None,
    )

    return TemplateMessage(altText="デジモン図鑑", template=template, quickReply=None)
