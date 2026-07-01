"""Loader-workflows: read-by-naming-convention -> interpolate/transform -> ready data.

This is the L3 home for *data-returning compositions* — functions that load one
or more files by Gkeyll's naming conventions, run them through ``ops`` verbs, and
return a ready :class:`~postgkyl.data.GData` / ``DatasetGroup`` for further array
math and plotting. They are the bodies behind the ``pg.load.<workflow>`` methods
(``loader.py``) and their matching thin CLI commands; both front-ends delegate
*down* into here.

Kept distinct from :mod:`postgkyl.gk`, which is pure *reference* (constants,
enums, naming helpers, the quantity registry) and never orchestrates ``ops``.
Loader-workflows compose; reference is consulted. Sibling to L4 ``apps/``, which
houses the *figure/analysis-returning* compositions.

Submodules import ``ops``/``data`` lazily inside their functions to keep package
import cheap and cycle-free, so this ``__init__`` intentionally re-exports
nothing.
"""
