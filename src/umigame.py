"""Shim to delegate umigame utilities to `src.domain.umigame`.

This keeps existing imports working while enabling an incremental migration of
the real implementation into `src/domain/`.
"""

from .domain.umigame import UMIGAME_STATE, is_closed_question

__all__ = ['UMIGAME_STATE', 'is_closed_question']
