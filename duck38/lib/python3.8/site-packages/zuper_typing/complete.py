from typing import Tuple

from zuper_commons.types import ZTypeError
from zuper_typing import (
    asdict_not_recursive,
    is_CustomDict,
    is_CustomList,
    is_CustomSet,
    is_CustomTuple,
    is_dataclass_instance,
)

__all__ = ["check_complete_types", "NotCompleteType"]


class NotCompleteType(ZTypeError):
    pass


def check_complete_types(x: object, prefix: Tuple[str, ...] = (), orig=None):
    if orig is None:
        orig = x

    if isinstance(x, dict):
        T = type(x)
        if not is_CustomDict(type(x)):
            raise NotCompleteType("Found", w=prefix, T=T, x=x, orig=orig)
        for k, v in x.items():
            check_complete_types(v, prefix=prefix + (k,), orig=orig)
    if isinstance(x, list):
        T = type(x)
        if not is_CustomList(type(x)):
            raise NotCompleteType("Found", w=prefix, T=T, x=x, orig=orig)
        for i, v in enumerate(x):
            check_complete_types(v, prefix=prefix + (str(i),), orig=orig)
    if isinstance(x, tuple):
        T = type(x)
        if not is_CustomTuple(type(x)):
            raise NotCompleteType("Found", w=prefix, T=T, x=x, orig=orig)
        for i, v in enumerate(x):
            check_complete_types(v, prefix=prefix + (str(i),), orig=orig)
    if isinstance(x, set):
        T = type(x)
        if not is_CustomSet(type(x)):
            raise NotCompleteType("Found", w=prefix, T=T, x=x, orig=orig)
        for i, v in enumerate(x):
            check_complete_types(v, prefix=prefix + (str(i),), orig=orig)
    elif is_dataclass_instance(x):
        for k, v in asdict_not_recursive(x).items():
            check_complete_types(v, prefix=prefix + (k,), orig=orig)
