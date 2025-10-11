"""Shim to delegate openai helpers to `src.domain.services.openai_helpers`.

This preserves backwards compatibility while we migrate implementation into
the domain/ hierarchy.
"""

from .domain.services.openai_helpers import (
    get_chatgpt_meal_suggestion,
    call_openai_yesno,
    call_openai_yesno_with_secret,
    generate_umigame_puzzle,
)

__all__ = [
    'get_chatgpt_meal_suggestion',
    'call_openai_yesno',
    'call_openai_yesno_with_secret',
    'generate_umigame_puzzle',
]
