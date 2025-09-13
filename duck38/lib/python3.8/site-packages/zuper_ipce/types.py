from datetime import datetime
from typing import Dict, List, Union

from zuper_typing import get_NewType_arg, is_Any, is_NewType, TypeLike

__all__ = ["IPCE", "TypeLike", "ModuleName", "QualName", "is_unconstrained"]

IPCE = Union[int, str, float, bytes, datetime, List["IPCE"], Dict[str, "IPCE"], type(None)]

ModuleName = QualName = str

_ = TypeLike


def is_unconstrained(t: TypeLike):
    assert t is not None
    return is_Any(t) or (t is object)


def get_effective_type(K):
    """ unwrap the NewType aliases"""
    if is_NewType(K):
        return get_effective_type(get_NewType_arg(K))
    return K
