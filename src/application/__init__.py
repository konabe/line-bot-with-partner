"""Application layer package.

Place use-case orchestration here. Initially acts as a shim to keep imports working
while we migrate code into DDD structure.
"""

from ..app import app as flask_app

__all__ = ['flask_app']
