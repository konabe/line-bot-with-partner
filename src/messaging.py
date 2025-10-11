"""Backward-compatible shim for messaging functions.

Delegates to `src.infrastructure` adapter management. This keeps existing
imports working while allowing adapters to be swapped for tests.
"""

from .infrastructure import init_messaging_api, safe_reply_message, safe_push_message

__all__ = ['init_messaging_api', 'safe_reply_message', 'safe_push_message']
