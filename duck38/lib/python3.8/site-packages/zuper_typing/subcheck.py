from dataclasses import dataclass, field, is_dataclass
from datetime import datetime
from decimal import Decimal
from functools import reduce
from numbers import Number
from typing import Any, cast, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Type, TypeVar

import numpy as np

from zuper_commons.text import indent
from zuper_commons.types import (
    ZAssertionError,
    ZException,
    ZNotImplementedError,
    ZTypeError,
    ZValueError,
)
from . import logger
from .aliases import TypeLike
from .annotations_tricks import (
    get_DictLike_args,
    get_FixedTupleLike_args,
    get_ForwardRef_arg,
    get_Iterable_arg,
    get_ListLike_arg,
    get_NewType_arg,
    get_NewType_name,
    get_Optional_arg,
    get_Sequence_arg,
    get_SetLike_arg,
    get_tuple_types,
    get_Type_arg,
    get_TypeVar_name,
    get_Union_args,
    get_VarTuple_arg,
    is_Any,
    is_Callable,
    is_ClassVar,
    is_DictLike,
    is_FixedTupleLike,
    is_ForwardRef,
    is_Iterable,
    is_List,
    is_ListLike,
    is_Optional,
    is_Sequence,
    is_SetLike,
    is_TupleLike,
    is_Type,
    is_TypeVar,
    is_Union,
    is_VarTuple,
    make_dict,
    make_Tuple,
    MyStr,
)
from .constants import ANNOTATIONS_ATT, ZuperTypingGlobals
from .literal import get_Literal_args, is_Literal, make_Literal
from .my_intersection import get_Intersection_args, is_Intersection
from .type_algebra import Matches, type_sup
from .uninhabited import is_Uninhabited

__all__ = ["can_be_used_as2", "value_liskov", "CanBeUsed", "check_value_liskov", "type_liskov"]


@dataclass
class CanBeUsed:
    result: bool
    why: str
    M: Matches
    matches: Optional[Dict[str, type]] = None

    reasons: "Dict[str, CanBeUsed]" = field(default_factory=dict)

    def __post_init__(self):
        assert isinstance(self.M, Matches), self
        self.matches = self.M.get_matches()
        self.reasons = DictStrCan(self.reasons)

    def __bool__(self):
        return self.result


DictStrCan = make_dict(str, CanBeUsed)


class CanBeUsedCache:
    can_be_used_cache = {}


from .annotations_tricks import is_NewType
from .get_patches_ import is_placeholder


def type_liskov(
    T1: TypeLike,
    T2: TypeLike,
    matches: Optional[Matches] = None,
    assumptions0: Tuple[Tuple[Any, Any], ...] = (),
    allow_is_shortcut: bool = True,
) -> CanBeUsed:
    if matches is None:
        matches = Matches()
    else:
        assert isinstance(matches, Matches), matches

    if is_placeholder(T1) or is_placeholder(T2):
        msg = "cannot compare classes with 'Placeholder' in the name (reserved internally)."
        raise ZValueError(msg, T1=T1, T2=T2)
    if is_Any(T2):
        return CanBeUsed(True, "Any", matches)
    if is_Any(T1):
        return CanBeUsed(True, "Any", matches)

    if is_Uninhabited(T1):
        return CanBeUsed(True, "Empty", matches)

    if (T1, T2) in assumptions0:
        return CanBeUsed(True, "By assumption", matches)

    if allow_is_shortcut:
        if (T1 is T2) or (T1 == T2):
            return CanBeUsed(True, "equal", matches)

    # redundant with above
    # if is_Any(T1) or is_Any(T2):
    #     return CanBeUsed(True, "Any ignores everything", matches)
    if T2 is object:
        return CanBeUsed(True, "object is the top", matches)
    # cop out for the easy cases
    assumptions = assumptions0 + ((T1, T2),)

    if is_NewType(T1) and is_NewType(T2):
        # special case of same alias
        t1 = get_NewType_arg(T1)
        t2 = get_NewType_arg(T2)
        n1 = get_NewType_name(T1)
        n2 = get_NewType_name(T2)
        res = can_be_used_as2(t1, t2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)
        if res:
            if n1 == n2:
                return res

    if is_NewType(T2):
        T2 = get_NewType_arg(T2)
    if is_Literal(T1):
        v1 = get_Literal_args(T1)
        if is_Literal(T2):
            v2 = get_Literal_args(T2)
            included = all(any(x1 == x2 for x2 in v2) for x1 in v1)
            if included:
                return CanBeUsed(True, "included", matches)
            else:
                return CanBeUsed(False, "not included", matches)
        else:
            t1 = type(v1[0])
            return can_be_used_as2(t1, T2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)

            # logger.info(f'can_be_used_as\n {T1} {T2}\n {assumptions0}')
    if is_Literal(T2):
        return CanBeUsed(False, "T1 not literal", matches)

    if T1 is type(None):
        if is_Optional(T2):
            return CanBeUsed(True, "", matches)
        # This never happens because it is caught by T1 is T2
        elif T2 is type(None):
            return CanBeUsed(True, "", matches)
        else:
            msg = f"Needs type(None), got {T2}"
            return CanBeUsed(False, msg, matches)

    if is_Union(T1):
        if is_Union(T2):
            if get_Union_args(T1) == get_Union_args(T2):
                return CanBeUsed(True, "same", matches)
        # can_be_used(Union[A,B], C)
        # == can_be_used(A,C) and can_be_used(B,C)

        for t in get_Union_args(T1):
            can = can_be_used_as2(t, T2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)
            # logger.info(f'can_be_used_as t = {t} {T2}')
            if not can.result:
                msg = f"Cannot match {t}"
                return CanBeUsed(False, msg, matches)

        return CanBeUsed(True, "", matches)

    if is_Union(T2):
        reasons = []
        for t in get_Union_args(T2):
            can = can_be_used_as2(T1, t, matches, assumptions, allow_is_shortcut=allow_is_shortcut)
            if can.result:
                return CanBeUsed(True, f"union match with {t} ", can.M)
            reasons.append(f"- {t}: {can.why}")

        msg = f"Cannot use {T1} as any of {T2}:\n" + "\n".join(reasons)
        return CanBeUsed(False, msg, matches)

    if is_TypeVar(T2):
        n2 = get_TypeVar_name(T2)
        if is_TypeVar(T1):
            n1 = get_TypeVar_name(T1)
            if n1 == n2:
                # TODO: intersection of bounds
                return CanBeUsed(True, "", matches)
            else:
                matches = matches.must_be_subtype_of(n1, T2)
                # raise ZNotImplementedError(T1=T1,T2=T2)

        matches = matches.must_be_supertype_of(n2, T1)
        return CanBeUsed(True, "", matches)

    if is_Intersection(T1):
        if is_Intersection(T2):
            if get_Intersection_args(T1) == get_Intersection_args(T2):
                return CanBeUsed(True, "same", matches)

        # Int[a, b] <= Int[C, D]
        # = Int[a, b] <= C  Int[a, b] <= D
        for t2 in get_Intersection_args(T2):
            can = can_be_used_as2(T1, t2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)
            # logger.info(f'can_be_used_as t = {t} {T2}')
            if not can.result:
                msg = f"Cannot match {t2}"
                return CanBeUsed(False, msg, matches)

        return CanBeUsed(True, "", matches)

    if is_Intersection(T2):
        # a <= Int[C, D]
        # = a <= C  and a <= D

        reasons = []
        for t2 in get_Intersection_args(T2):
            can = can_be_used_as2(T1, t2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)
            if not can.result:
                return CanBeUsed(False, f"no match  {T1} {t2} ", can.M)

        msg = f"Cannot use {T1} as any of {T2}:\n" + "\n".join(reasons)
        return CanBeUsed(False, msg, matches)

    if is_TypeVar(T1):
        n1 = get_TypeVar_name(T1)
        matches = matches.must_be_subtype_of(n1, T2)
        return CanBeUsed(True, "Any", matches)
        # TODO: not implemented

    if is_Optional(T1):
        t1 = get_Optional_arg(T1)

        if is_Optional(T2):
            t2 = get_Optional_arg(T2)
            return can_be_used_as2(t1, t2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)
        if T2 is type(None):
            return CanBeUsed(True, "", matches)

        return can_be_used_as2(t1, T2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)

    if is_Optional(T2):
        t2 = get_Optional_arg(T2)
        if is_Optional(T1):
            t1 = get_Optional_arg(T1)
            return can_be_used_as2(t1, t2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)

        return can_be_used_as2(T1, t2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)

    # ---- concrete

    if T1 is MyStr:
        if T2 in (str, MyStr):
            return CanBeUsed(True, "str ~ MyStr", matches)
        else:
            return CanBeUsed(False, "MyStr wants str", matches)
    if T2 is MyStr:
        if T1 in (str, MyStr):
            return CanBeUsed(True, "str ~ MyStr", matches)
        else:
            return CanBeUsed(False, "MyStr wants str", matches)

    trivial = (int, str, bool, Decimal, datetime, float, Number)

    if T1 in trivial:
        if T2 not in trivial:
            return CanBeUsed(False, "A trivial cannot be a subclass of non-trivial", matches)

    if T2 in trivial:
        if T1 in trivial + (np.float32, np.float64):
            return CanBeUsed(issubclass(T1, T2), "trivial subclass", matches)
            # raise ZNotImplementedError(T1=T1, T2=T2)

        return CanBeUsed(False, f"Not a trivial type (T1={T1}, T2={T2})", matches)
    if is_DictLike(T2):

        if not is_DictLike(T1):
            msg = f"Expecting a dictionary, got {T1}"
            return CanBeUsed(False, msg, matches)
        else:
            T1 = cast(Type[Dict], T1)
            T2 = cast(Type[Dict], T2)
            K1, V1 = get_DictLike_args(T1)
            K2, V2 = get_DictLike_args(T2)

            rk = can_be_used_as2(K1, K2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)
            if not rk:
                return CanBeUsed(False, f"keys {K1} {K2}: {rk}", matches)

            rv = can_be_used_as2(V1, V2, rk.M, assumptions, allow_is_shortcut=allow_is_shortcut)
            if not rv:
                return CanBeUsed(False, f"values {V1} {V2}: {rv}", matches)

            return CanBeUsed(True, f"ok: {rk} {rv}", rv.M)
    else:
        if is_DictLike(T1):
            msg = "A Dict needs a dictionary"
            return CanBeUsed(False, msg, matches)

    assert not is_Union(T2)

    if is_dataclass(T1):
        if not is_dataclass(T2):
            msg = "Second is not dataclass "
            return CanBeUsed(False, msg, matches)
    from .zeneric2 import StructuralTyping

    if isinstance(T2, StructuralTyping):
        if not isinstance(T1, StructuralTyping):
            msg = "Not structural typing"
            return CanBeUsed(False, msg, matches)

    if is_dataclass(T2):
        if not is_dataclass(T1):
            if ZuperTypingGlobals.verbose:
                msg = f"Expecting dataclass to match to {T2}, got something that is not a " f"dataclass: {T1}"
                msg += f"  union: {is_Union(T1)}"
            else:  # pragma: no cover
                msg = "not dataclass"
            return CanBeUsed(False, msg, matches)
        # h1 = get_type_hints(T1)
        # h2 = get_type_hints(T2)

        key = (T1.__module__, T1.__qualname__, T2.__module__, T2.__qualname__)
        if key in CanBeUsedCache.can_be_used_cache:
            return CanBeUsedCache.can_be_used_cache[key]

        h1 = getattr(T1, ANNOTATIONS_ATT, {})
        h2 = getattr(T2, ANNOTATIONS_ATT, {})

        for k, v2 in h2.items():
            if not k in h1:
                if ZuperTypingGlobals.verbose:
                    msg = (
                        f'Type {T2}\n requires field "{k}" \n  of type {v2} \n  but {T1} does '
                        f"not have it. "
                    )
                else:  # pragma: no cover
                    msg = k
                res = CanBeUsed(False, msg, matches)
                CanBeUsedCache.can_be_used_cache[key] = res
                return res

            v1 = h1[k]

            # XXX
            if is_ClassVar(v1):
                continue

            can = can_be_used_as2(v1, v2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)
            if not can.result:
                if ZuperTypingGlobals.verbose:
                    msg = (
                        f'Type {T2}\n  requires field "{k}"\n  of type\n       {v2} \n  but'
                        + f" {T1}\n  has annotated it as\n       {v1}\n  which cannot be used. "
                    )
                    msg += "\n\n" + f"assumption: {assumptions}"
                    msg += "\n\n" + indent(can.why, "> ")
                else:  # pragma: no cover
                    msg = ""
                res = CanBeUsed(False, msg, matches)
                CanBeUsedCache.can_be_used_cache[key] = res
                return res

        res = CanBeUsed(True, "dataclass", matches)
        CanBeUsedCache.can_be_used_cache[key] = res
        return res

    if is_FixedTupleLike(T1):
        T1 = cast(Type[Tuple], T1)
        if not is_TupleLike(T2):
            msg = "A tuple can only be used as a tuple"
            return CanBeUsed(False, msg, matches)
        T2 = cast(Type[Tuple], T2)
        if is_FixedTupleLike(T2):

            t1s = get_tuple_types(T1)
            t2s = get_tuple_types(T2)
            if len(t1s) != len(t2s):
                msg = "Different length"
                return CanBeUsed(False, msg, matches)
            for i, (t1, t2) in enumerate(zip(t1s, t2s)):
                can = can_be_used_as2(t1, t2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)
                if not can:
                    return CanBeUsed(False, f"{t1} {t2}", matches, reasons={str(i): can})
                matches = can.M
            return CanBeUsed(True, "", matches)
        elif is_VarTuple(T2):
            t1s = get_tuple_types(T1)
            if len(t1s) == 0:
                return CanBeUsed(True, "Empty tuple counts as var tuple", matches)
            T = get_VarTuple_arg(T2)
            tmax = reduce(type_sup, t1s)
            can = can_be_used_as2(tmax, T, matches, assumptions, allow_is_shortcut=allow_is_shortcut)
            if not can:
                msg = "The sup of the types in T1 is not a sub of T"
                return CanBeUsed(False, msg, matches, reasons={"": can})
            return CanBeUsed(True, "", matches)
        else:
            raise ZAssertionError(T1=T1, T2=T2)
    if is_VarTuple(T1):
        T1 = cast(Type[Tuple], T1)
        if not is_VarTuple(T2):
            msg = "A var tuple can only be used as a var tuple"
            return CanBeUsed(False, msg, matches)
        T2 = cast(Type[Tuple], T2)
        t1 = get_VarTuple_arg(T1)
        t2 = get_VarTuple_arg(T2)
        can = can_be_used_as2(t1, t2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)
        if not can:
            return CanBeUsed(False, f"{t1} {t2}", matches, reasons={"": can})
        else:
            return CanBeUsed(True, "", matches)

    if is_TupleLike(T2):
        assert not is_TupleLike(T1)
        return CanBeUsed(False, f"Not a tuple type T1={T1} T2={T2}", matches)

    if is_Any(T1):
        assert not is_Union(T2)
        if not is_Any(T2):
            msg = "Any is the top"
            return CanBeUsed(False, msg, matches)

    if is_ListLike(T2):
        if not is_ListLike(T1):
            msg = "A List can only be used as a List"
            return CanBeUsed(False, msg, matches)

        T1 = cast(Type[List], T1)
        T2 = cast(Type[List], T2)
        t1 = get_ListLike_arg(T1)
        t2 = get_ListLike_arg(T2)
        # print(f'matching List with {t1} {t2}')
        can = can_be_used_as2(t1, t2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)

        if not can.result:
            return CanBeUsed(False, f"{t1} {T2}", matches)

        return CanBeUsed(True, "", can.M)

    if is_Callable(T2):
        if not is_Callable(T1):
            return CanBeUsed(False, "not callable", matches)

        raise ZNotImplementedError(T1=T1, T2=T2)

    if is_ForwardRef(T1):
        n1 = get_ForwardRef_arg(T1)
        if is_ForwardRef(T2):
            n2 = get_ForwardRef_arg(T2)
            if n1 == n2:
                return CanBeUsed(True, "", matches)
            else:
                return CanBeUsed(False, "different name", matches)
        else:
            return CanBeUsed(False, "not fw ref", matches)
    if is_ForwardRef(T2):
        n2 = get_ForwardRef_arg(T2)
        if hasattr(T1, "__name__"):
            if T1.__name__ == n2:
                return CanBeUsed(True, "", matches)
            else:
                return CanBeUsed(False, "different name", matches)

    if is_Iterable(T2):

        T2 = cast(Type[Iterable], T2)
        t2 = get_Iterable_arg(T2)

        if is_Iterable(T1):
            T1 = cast(Type[Iterable], T1)
            t1 = get_Iterable_arg(T1)
            return can_be_used_as2(t1, t2, matches, allow_is_shortcut=allow_is_shortcut)

        if is_SetLike(T1):
            T1 = cast(Type[Set], T1)
            t1 = get_SetLike_arg(T1)
            return can_be_used_as2(t1, t2, matches, allow_is_shortcut=allow_is_shortcut)

        if is_ListLike(T1):
            T1 = cast(Type[List], T1)
            t1 = get_ListLike_arg(T1)
            return can_be_used_as2(t1, t2, matches, allow_is_shortcut=allow_is_shortcut)

        if is_DictLike(T1):
            T1 = cast(Type[Dict], T1)
            K, V = get_DictLike_args(T1)
            t1 = Tuple[K, V]
            return can_be_used_as2(t1, t2, matches, allow_is_shortcut=allow_is_shortcut)

        return CanBeUsed(False, "expect iterable", matches)

    if is_SetLike(T2):
        if not is_SetLike(T1):
            msg = "A Set can only be used as a Set"
            return CanBeUsed(False, msg, matches)

        T1 = cast(Type[Set], T1)
        T2 = cast(Type[Set], T2)
        t1 = get_SetLike_arg(T1)
        t2 = get_SetLike_arg(T2)
        # print(f'matching List with {t1} {t2}')
        can = can_be_used_as2(t1, t2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)

        if not can.result:
            return CanBeUsed(False, f"Set argument fails", matches, reasons={"set_arg": can})

        return CanBeUsed(True, "", can.M)

    if is_Sequence(T1):
        T1 = cast(Type[Sequence], T1)
        t1 = get_Sequence_arg(T1)

        if is_ListLike(T2):
            T2 = cast(Type[List], T2)
            t2 = get_ListLike_arg(T2)
            can = can_be_used_as2(t1, t2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)

            if not can.result:
                return CanBeUsed(False, f"{t1} {T2}", matches)

            return CanBeUsed(True, "", can.M)

        msg = f"Needs a Sequence[{t1}], got {T2}"
        return CanBeUsed(False, msg, matches)

    if isinstance(T1, type) and isinstance(T2, type):
        # NOTE: this didn't work with Number for whatever reason
        # NOTE: issubclass(A, B) == type(T2).__subclasscheck__(T2, T1)
        # a0 = type.__subclasscheck__(T2, T1)
        # b0 = type.__subclasscheck__(T1, T2)
        logger.info(T1=T1, T2=T2)

        a = issubclass(T1, T2)
        # assert a0 == a and b0 == b, (T1, T2, a0, b0, a, b)
        if a:
            return CanBeUsed(True, f"type.__subclasscheck__ {T1} {T2}", matches)
        else:
            msg = f"Type {T1} is not a subclass of {T2} "
            # msg += f"; viceversa : {b}"
            return CanBeUsed(False, msg, matches)

    if is_List(T1):
        msg = f"Needs a List, got {T2}"
        return CanBeUsed(False, msg, matches)

    if T2 is type(None):
        msg = f"Needs type(None), got {T1}"
        return CanBeUsed(False, msg, matches)

    if is_NewType(T1):
        n1 = get_NewType_arg(T1)
        if is_NewType(T2):
            n2 = get_NewType_arg(T2)
            return can_be_used_as2(n1, n2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)
            # if n1 == n2:
            #     return CanBeUsed(True, "", matches)
            # else:
            #     raise ZNotImplementedError(T1=T1, T2=T2)
        else:
            return can_be_used_as2(n1, T2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)

    if is_Type(T1):
        if not is_Type(T2):
            return CanBeUsed(False, f"Not a Type[X], T1={T1}, T2={T2}", matches)
        sc1 = get_Type_arg(T1)
        sc2 = get_Type_arg(T2)
        return can_be_used_as2(sc1, sc2, matches, assumptions, allow_is_shortcut=allow_is_shortcut)

    # msg = f"{T1} ? {T2}"  # pragma: no cover
    raise ZNotImplementedError(T1=T1, T2=T2)


can_be_used_as2 = type_liskov


def value_liskov(a: object, T: TypeLike) -> CanBeUsed:
    if is_Literal(T):
        res = a in get_Literal_args(T)  # XXX
        return CanBeUsed(res, "literal", Matches())

    if is_DictLike(T):
        return value_liskov_DictLike(a, cast(Type[Dict], T))
    if is_SetLike(T):
        return value_liskov_SetLike(a, cast(Type[Set], T))
    if is_ListLike(T):
        return value_liskov_ListLike(a, cast(Type[List], T))
    if is_FixedTupleLike(T):
        return value_liskov_FixedTupleLike(a, cast(Type[Tuple], T))
    if is_VarTuple(T):
        return value_liskov_VarTuple(a, cast(Type[Tuple], T))
    if is_Union(T):
        return value_liskov_Union(a, T)
    S = ztype(a)
    return can_be_used_as2(S, T)


def value_liskov_Union(a: object, T: type) -> CanBeUsed:
    ts = get_Union_args(T)
    reasons = {}
    for i, t in enumerate(ts):
        ok_k = value_liskov(a, t)
        if ok_k:
            msg = f"Match #{i}"
            return CanBeUsed(True, msg, ok_k.M, ok_k.matches, reasons={str(i): ok_k})
        reasons[str(i)] = ok_k
    return CanBeUsed(False, "No match", Matches(), reasons=reasons)


def value_liskov_DictLike(a: object, T: Type[Dict]) -> CanBeUsed:
    K, V = get_DictLike_args(cast(Type[Dict], T))
    if not isinstance(a, dict):
        return CanBeUsed(False, "not a dict", Matches())
    for k, v in a.items():
        ok_k = value_liskov(k, K)
        if not ok_k:
            msg = f"Invalid key: {ok_k}"
            return CanBeUsed(False, msg, Matches())
        ok_v = value_liskov(v, V)
        if not ok_v:
            msg = f"Invalid value: {ok_v}"
            return CanBeUsed(False, msg, Matches())
    return CanBeUsed(True, "ok", Matches())


def value_liskov_SetLike(a: object, T: Type[Set]) -> CanBeUsed:
    V = get_SetLike_arg(T)
    if not isinstance(a, set):
        return CanBeUsed(False, "not a set", Matches())
    for i, v in enumerate(a):
        ok = value_liskov(v, V)
        if not ok:
            msg = f"Invalid value #{i}: {ok}"
            return CanBeUsed(False, msg, Matches())

    return CanBeUsed(True, "ok", Matches())


def value_liskov_ListLike(a: object, T: Type[List]) -> CanBeUsed:
    V = get_ListLike_arg(T)
    if not isinstance(a, list):
        return CanBeUsed(False, f"not a list: {type(a)}", Matches())
    for i, v in enumerate(a):
        ok = value_liskov(v, V)
        if not ok:
            msg = f"Invalid value #{i}: {ok}"
            return CanBeUsed(False, msg, Matches())

    return CanBeUsed(True, "ok", Matches())


def value_liskov_VarTuple(a: object, T: Type[Tuple]) -> CanBeUsed:
    V = get_VarTuple_arg(T)
    if not isinstance(a, tuple):
        return CanBeUsed(False, "not a tuple", Matches())
    for i, v in enumerate(a):
        ok = value_liskov(v, V)
        if not ok:
            msg = f"Invalid value #{i}"
            return CanBeUsed(False, msg, reasons={str(i): ok}, M=Matches())
    return CanBeUsed(True, "ok", Matches())


def value_liskov_FixedTupleLike(a: object, T: Type[Tuple]) -> CanBeUsed:
    VS = get_FixedTupleLike_args(T)
    if not isinstance(a, tuple):
        return CanBeUsed(False, "not a tuple", Matches())
    if len(a) != len(VS):
        return CanBeUsed(False, "wrong length", Matches())

    for i, (v, V) in enumerate(zip(a, VS)):
        ok = value_liskov(v, V)
        if not ok:
            msg = f"Invalid value #{i}"
            return CanBeUsed(False, msg, reasons={str(i): ok}, M=Matches())

    return CanBeUsed(True, "ok", Matches())


X = TypeVar("X")


def check_value_liskov(ob: object, T: Type[X]) -> X:
    try:
        ok = value_liskov(ob, T)
    except ZException as e:
        msg = "Could not run check_value_liskov() successfully."
        raise ZAssertionError(msg, ob=ob, Tob=type(ob), T=T) from e
    if not ok:
        raise ZTypeError(ob=ob, T=T, ok=ok)
    else:
        return cast(T, ob)


def ztype(a: object) -> type:
    if type(a) is tuple:
        a = cast(tuple, a)
        ts = tuple(make_Literal(_) for _ in a)
        return make_Tuple(*ts)
    # todo: substitute tuple, list, dict with estimated
    return type(a)
