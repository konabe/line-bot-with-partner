"""Infrastructure package exports for messaging helpers.

The concrete implementation lives in :mod:`.messaging_infrastructure` to keep
package initialization lightweight and to make testing easier.
"""

from .messaging_infrastructure import MessagingInfrastructure

__all__ = ["MessagingInfrastructure"]
