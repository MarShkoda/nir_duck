import typing
from typing import Union

from .constants import PYTHON_36

if PYTHON_36:  # pragma: no cover
    TypeLike = type
else:
    TypeLike = Union[type, typing._SpecialForm]

__all__ = ["TypeLike"]
