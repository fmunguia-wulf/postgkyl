"""High-level, scriptable pgkyl API.

Re-exports the generated :class:`PgkylSession` so it can be imported directly
from the package:

    from postgkyl.api import PgkylSession
"""

from postgkyl.api.api import PgkylSession

__all__ = ["PgkylSession"]
