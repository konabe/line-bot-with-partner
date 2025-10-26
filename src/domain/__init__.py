"""Domain layer package.

This package re-exports domain-relevant pieces from the current codebase
to allow an incremental migration to a DDD layout.
"""

from ..infrastructure.openai_helpers import OpenAIClient

__all__ = [
    'OpenAIClient',
]
