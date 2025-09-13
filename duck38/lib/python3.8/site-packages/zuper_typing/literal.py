import typing
from typing import Tuple

from .constants import PYTHON_36, PYTHON_37

if PYTHON_36 or PYTHON_37:
    from typing_extensions import Literal
else:
    from typing import Literal

from zuper_commons.types import ZValueError
from .aliases import TypeLike
from .constants import PYTHON_36

__all__ = ["make_Literal", "is_Literal", "get_Literal_args"]


def make_Literal(*values: object) -> TypeLike:
    if not values:
        msg = "A literal needs at least one value"
        raise ZValueError(msg, values=values)
    types = set(type(_) for _ in values)
    if len(types) > 1:
        msg = "We only allow values of the same type."
        raise ZValueError(msg, values=values, types=types)
    values = tuple(sorted(values))
    # noinspection PyTypeHints
    return Literal[values]


def is_Literal(x: TypeLike) -> bool:
    if PYTHON_36:
        return type(x).__name__ == "_Literal"
    else:

        # noinspection PyUnresolvedReferences
        return isinstance(x, typing._GenericAlias) and (getattr(x, "__origin__") is Literal)


def get_Literal_args(x: TypeLike) -> Tuple[TypeLike, ...]:
    assert is_Literal(x)
    if PYTHON_36:
        # noinspection PyUnresolvedReferences
        return x.__values__
    else:
        return getattr(x, "__args__")
