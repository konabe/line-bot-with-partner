"""Domain layer package.

This package re-exports domain-relevant pieces from the current codebase
to allow an incremental migration to a DDD layout.
"""

from .umigame import UMIGAME_STATE, is_closed_question
from ..infrastructure.openai_helpers import OpenAIClient

__all__ = [
    'UMIGAME_STATE',
    'is_closed_question',
    'OpenAIClient',
]
