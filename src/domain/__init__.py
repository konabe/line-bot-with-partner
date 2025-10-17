"""Domain layer package.

This package re-exports domain-relevant pieces from the current codebase
to allow an incremental migration to a DDD layout.
"""

from .umigame import UMIGAME_STATE, is_closed_question
from ..infrastructure.openai_helpers import (
    get_chatgpt_meal_suggestion,
    call_openai_yesno,
    call_openai_yesno_with_secret,
    generate_umigame_puzzle,
)

__all__ = [
    'UMIGAME_STATE',
    'is_closed_question',
    'get_chatgpt_meal_suggestion',
    'call_openai_yesno',
    'call_openai_yesno_with_secret',
    'generate_umigame_puzzle',
]
