from dataclasses import Field, fields, is_dataclass
from typing import Dict, List, Optional, Set, Tuple, Type, TypeVar

from zuper_commons.types import ZValueError
from . import dataclass
from .annotations_tricks import (
    get_VarTuple_arg,
    is_VarTuple,
)
from .dataclass_info import is_dataclass_instance
from .annotations_tricks import (
    get_DictLike_args,
    get_ListLike_arg,
    get_SetLike_arg,
    is_DictLike,
    is_ListLike,
    is_SetLike,
    is_FixedTupleLike,
    get_FixedTupleLike_args,
)

__all__ = ["eq", "EqualityResult"]

X = TypeVar("X")


@dataclass
class EqualityResult:
    result: bool
    why: "Dict[str, EqualityResult]"
    a: object
    b: object
    msg: Optional[str] = None

    def __bool__(self) -> bool:
        return self.result


def eq(T: Type[X], a: X, b: X) -> EqualityResult:
    # logger.info("eq", T=T, a=a, b=b)
    # todo: tuples
    if is_dataclass(T):
        return eq_dataclass(T, a, b)
    elif is_ListLike(T):
        return eq_listlike(T, a, b)
    elif is_FixedTupleLike(T):
        return eq_tuplelike_fixed(T, a, b)
    elif is_VarTuple(T):
        return eq_tuplelike_var(T, a, b)
    elif is_DictLike(T):
        return eq_dictlike(T, a, b)
    elif is_SetLike(T):
        return eq_setlike(T, a, b)
    else:
        if not (a == b):
            return EqualityResult(result=False, a=a, b=b, why={}, msg="by equality")
        else:
            return EqualityResult(result=True, a=a, b=b, why={})


K = TypeVar("K")
V = TypeVar("V")


def eq_dictlike(T: Type[Dict[K, V]], a: Dict[K, V], b: Dict[K, V]) -> EqualityResult:
    k1 = set(a)
    k2 = set(b)
    if k1 != k2:
        return EqualityResult(result=False, a=a, b=b, why={}, msg="different keys")
    _, V = get_DictLike_args(T)

    why = {}
    for k in k1:
        va = a[k]
        vb = b[k]
        r = eq(V, va, vb)
        if not r.result:
            why[k] = r

    result = len(why) == 0
    return EqualityResult(result=result, why=(why), a=a, b=b)


def eq_listlike(T: Type[List[V]], a: List[V], b: List[V]) -> EqualityResult:
    k1 = len(a)
    k2 = len(b)
    if k1 != k2:
        return EqualityResult(result=False, a=a, b=b, why={}, msg="different length")
    V = get_ListLike_arg(T)

    why = {}
    for i in range(k1):
        va = a[i]
        vb = b[i]
        r = eq(V, va, vb)
        if not r.result:
            why[str(i)] = r

    result = len(why) == 0
    return EqualityResult(result=result, why=why, a=a, b=b)


def eq_setlike(T: Type[Set[V]], a: Set[V], b: Set[V]) -> EqualityResult:
    k1 = len(a)
    k2 = len(b)
    if k1 != k2:
        return EqualityResult(result=False, a=a, b=b, why={}, msg="different length")
    V = get_SetLike_arg(T)

    why = {}

    for i, va in enumerate(a):
        for vb in b:
            r = eq(V, va, vb)
            if r:
                break
        else:
            why["a" + str(i)] = EqualityResult(result=False, a=va, b=None, why={}, msg="Missing")

    for i, vb in enumerate(b):
        for va in a:
            r = eq(V, va, vb)
            if r:
                break
        else:
            why["b" + str(i)] = EqualityResult(result=False, a=None, b=vb, why={}, msg="Missing")

    result = len(why) == 0
    return EqualityResult(result=result, why=why, a=a, b=b)


def eq_tuplelike_fixed(T: Type[Tuple], a: Tuple, b: Tuple) -> EqualityResult:
    assert is_FixedTupleLike(T), T
    args = get_FixedTupleLike_args(T)
    n = len(args)
    k1 = len(a)
    k2 = len(b)
    if not (k1 == k2 == n):
        return EqualityResult(result=False, a=a, b=b, why={}, msg="different length")

    why = {}
    for i, V in enumerate(args):
        va = a[i]
        vb = b[i]
        r = eq(V, va, vb)
        if not r.result:
            why[str(i)] = r

    result = len(why) == 0
    return EqualityResult(result=result, why=why, a=a, b=b)


def eq_tuplelike_var(T: Type[Tuple], a: Tuple, b: Tuple) -> EqualityResult:
    assert is_VarTuple(T), T
    V = get_VarTuple_arg(T)

    k1 = len(a)
    k2 = len(b)
    if not (k1 == k2):
        return EqualityResult(result=False, a=a, b=b, why={}, msg="different length")

    why = {}
    for i in range(k1):
        va = a[i]
        vb = b[i]
        r = eq(V, va, vb)
        if not r.result:
            why[str(i)] = r

    result = len(why) == 0
    return EqualityResult(result=result, why=why, a=a, b=b)


def eq_dataclass(T, a, b):
    if not is_dataclass(T):  # pragma: no cover
        raise ZValueError(T=T, a=a, b=b)

    if not is_dataclass_instance(a) or not is_dataclass_instance(b):
        return EqualityResult(result=False, why={}, a=a, b=b, msg="not even dataclasses")

    _fields: List[Field] = fields(T)
    why = {}
    for f in _fields:
        va = getattr(a, f.name)
        vb = getattr(b, f.name)

        res = eq(f.type, va, vb)
        if not res.result:
            why[f.name] = res

    result = len(why) == 0
    return EqualityResult(result=result, why=dict(why), a=a, b=b)
