import pytest
from src.umigame import is_closed_question


@pytest.mark.parametrize('text,expected', [
    ('これはテストですか', True),
    ('これはテストですか？', True),
    ('何が起きたの？', False),
    ('なぜそうなったのですか', False),
    ('できますか', True),
    ('これは何ですか', False),
    ('これでいい？', True),
    ('誰が来る？', False),
    ('明日行けますか？', True),
    ('量はどれくらい必要？', False),
    ('これは真実か', True),
    ('もう終わり？', True),
    ('どうやってやるの？', False),
    ('ありますか？', True),
])
def test_is_closed_question(text, expected):
    assert is_closed_question(text) == expected
