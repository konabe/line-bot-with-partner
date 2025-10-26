def create_pokemon_zukan_button_template(info):
    """SDK の TemplateMessage (ButtonsTemplate) を返す。SDK が無い場合は dict を返す。"""
    try:
        from linebot.v3.messaging import models

        type_text = ' / '.join(info.get('types') or []) if info.get('types') else '不明'
        image_url = info.get('image_url') or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png"
        title = f"No.{info.get('zukan_no')} {info.get('name')}"

        template = models.ButtonsTemplate(
            title=title,
            text=f"タイプ: {type_text}",
            thumbnail_image_url=image_url,
            actions=[models.URIAction(label='画像を見る', uri=image_url)],
        )
        return models.TemplateMessage(alt_text='ポケモン図鑑', template=template)
    except Exception:
        return
