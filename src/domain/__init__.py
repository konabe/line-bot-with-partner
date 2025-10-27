"""Domain layer package.

This package re-exports domain-relevant pieces from the current codebase
to allow an incremental migration to a DDD layout.

Use absolute imports so this package works consistently when the project is
loaded as a top-level package (for example when running the app as a module
or under different working directories).
"""

from src.infrastructure.adapters.openai_adapter import OpenAIAdapter

__all__ = [
    'OpenAIAdapter',
]
