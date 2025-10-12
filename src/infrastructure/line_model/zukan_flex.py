# ポケモン図鑑FLEX Message生成（SDK依存なし）
def create_pokemon_zukan_flex_dict(info):
    type_text = ' / '.join(info['types']) if info['types'] else '不明'
    flex = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": info['image_url'] or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png",
            "size": "xl",
            "aspectRatio": "1:1",
            "aspectMode": "cover"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"No.{info['zukan_no']} {info['name']}",
                    "weight": "bold",
                    "size": "xl",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": f"タイプ: {type_text}",
                    "size": "md",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": f"進化: {info['evolution']}",
                    "size": "sm",
                    "align": "center"
                }
            ]
        }
    }
    return flex
