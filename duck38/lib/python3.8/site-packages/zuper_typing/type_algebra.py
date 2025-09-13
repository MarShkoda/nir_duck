from dataclasses import dataclass, field, is_dataclass
from datetime import datetime
from decimal import Decimal
from functools import reduce
from typing import cast, Dict, List, Optional, Set, Tuple, Type

from zuper_commons.types import ZValueError
from .aliases import TypeLike
from .annotations_tricks import (
    get_DictLike_args,
    get_FixedTupleLike_args,
    get_ListLike_arg,
    get_Optional_arg,
    get_SetLike_arg,
    get_TypeVar_name,
    get_Union_args,
    get_VarTuple_arg,
    is_DictLike,
    is_FixedTupleLike,
    is_ListLike,
    is_Optional,
    is_SetLike,
    is_TypeVar,
    is_Union,
    is_VarTuple,
    make_dict,
    make_list,
    make_set,
    make_Tuple,
    make_Union,
    make_VarTuple,
    unroll_union,
)
from .common import DictStrType
from .my_intersection import get_Intersection_args, is_Intersection, make_Intersection
from .uninhabited import is_Uninhabited, make_Uninhabited

__all__ = ["type_inf", "type_sup", "Matches"]


def unroll_intersection(a: TypeLike) -> Tuple[TypeLike, ...]:
    if is_Intersection(a):
        return get_Intersection_args(a)
    else:
        return (a,)


def type_sup(a: TypeLike, b: TypeLike) -> TypeLike:
    assert a is not None
    assert b is not None
    assert not isinstance(a, tuple), a
    assert not isinstance(b, tuple), b

    if a is b or (a == b):
        return a

    if a is object or b is object:
        return object

    if is_Uninhabited(a):
        return b
    if is_Uninhabited(b):
        return a

    if a is type(None):
        if is_Optional(b):
            return b
        else:
            return Optional[b]
    if b is type(None):
        if is_Optional(a):
            return a
        else:
            return Optional[a]

    if is_Optional(a):
        return type_sup(type(None), type_sup(get_Optional_arg(a), b))
    if is_Optional(b):
        return type_sup(type(None), type_sup(get_Optional_arg(b), a))
    # if is_Union(a) and is_Union(b):  # XXX
    #     r = []
    #     r.extend(unroll_union(a))
    #     r.extend(unroll_union(b))
    #     return reduce(type_sup, r)
    #

    if is_Union(a) and is_Union(b):
        ta = unroll_union(a)
        tb = unroll_union(b)
        tva, oa = get_typevars(ta)
        tvb, ob = get_typevars(tb)
        tv = tuple(set(tva + tvb))
        oab = oa + ob
        if not oab:
            return make_Union(*tv)
        else:
            other = reduce(type_sup, oa + ob)
            os = unroll_union(other)
            return make_Union(*(tv + os))

    if (a, b) in [(bool, int), (int, bool)]:
        return int

    if is_ListLike(a) and is_ListLike(b):
        a = cast(Type[List], a)
        b = cast(Type[List], b)
        A = get_ListLike_arg(a)
        B = get_ListLike_arg(b)
        u = type_sup(A, B)
        return make_list(u)

    if is_SetLike(a) and is_SetLike(b):
        a = cast(Type[Set], a)
        b = cast(Type[Set], b)
        A = get_SetLike_arg(a)
        B = get_SetLike_arg(b)
        u = type_sup(A, B)
        return make_set(u)

    if is_DictLike(a) and is_DictLike(b):
        a = cast(Type[Dict], a)
        b = cast(Type[Dict], b)
        KA, VA = get_DictLike_args(a)
        KB, VB = get_DictLike_args(b)
        K = type_sup(KA, KB)
        V = type_sup(VA, VB)
        return make_dict(K, V)

    if is_VarTuple(a) and is_VarTuple(b):
        a = cast(Type[Tuple], a)
        b = cast(Type[Tuple], b)
        VA = get_VarTuple_arg(a)
        VB = get_VarTuple_arg(b)
        V = type_sup(VA, VB)
        return make_VarTuple(V)

    if is_FixedTupleLike(a) and is_FixedTupleLike(b):
        a = cast(Type[Tuple], a)
        b = cast(Type[Tuple], b)
        tas = get_FixedTupleLike_args(a)
        tbs = get_FixedTupleLike_args(b)
        ts = tuple(type_sup(ta, tb) for ta, tb in zip(tas, tbs))
        return make_Tuple(*ts)

    if is_dataclass(a) and is_dataclass(b):
        return type_sup_dataclass(a, b)

    if is_TypeVar(a) and is_TypeVar(b):
        if get_TypeVar_name(a) == get_TypeVar_name(b):
            return a

    return make_Union(a, b)

    # raise NotImplementedError(a, b)


def type_inf_dataclass(a: Type[dataclass], b: Type[dataclass]) -> Type[dataclass]:
    from .monkey_patching_typing import my_dataclass

    ann_a = a.__annotations__
    ann_b = b.__annotations__

    all_keys = set(ann_a) | set(ann_b)

    res = {}
    for k in all_keys:
        if k in ann_a and k not in ann_b:
            R = ann_a[k]
        elif k not in ann_a and k in ann_b:
            R = ann_b[k]
        else:
            VA = ann_a[k]
            VB = ann_b[k]
            R = type_inf(VA, VB)

        if is_Uninhabited(R):
            return R
        res[k] = R
    name = f"Int_{a.__name__}_{b.__name__}"
    T2 = my_dataclass(type(name, (), {"__annotations__": res, "__module__": "zuper_typing"}))
    return T2


def type_sup_dataclass(a: Type[dataclass], b: Type[dataclass]) -> Type[dataclass]:
    from .monkey_patching_typing import my_dataclass

    ann_a = a.__annotations__
    ann_b = b.__annotations__

    common_keys = set(ann_a) & set(ann_b)

    res = {}
    for k in common_keys:
        if k in ann_a and k not in ann_b:
            R = ann_a[k]
        elif k not in ann_a and k in ann_b:
            R = ann_b[k]
        else:
            VA = ann_a[k]
            VB = ann_b[k]
            R = type_sup(VA, VB)
        res[k] = R

    name = f"Join_{a.__name__}_{b.__name__}"
    T2 = my_dataclass(type(name, (), {"__annotations__": res, "__module__": "zuper_typing"}))
    return T2


def type_inf(a: TypeLike, b: TypeLike) -> TypeLike:
    try:
        res = type_inf0(a, b)
    except ZValueError as e:  # pragma: no cover
        raise
    #     raise ZValueError("problem", a=a, b=b) from e
    # if isinstance(res, tuple):
    #     raise ZValueError(a=a, b=b, res=res)
    return res


def get_typevars(a: Tuple[TypeLike, ...]) -> Tuple[Tuple, Tuple]:
    tv = []
    ts = []
    for _ in a:
        if is_TypeVar(_):
            tv.append(_)
        else:
            ts.append(_)
    return tuple(tv), tuple(ts)


def type_inf0(a: TypeLike, b: TypeLike) -> TypeLike:
    assert a is not None
    assert b is not None
    if isinstance(a, tuple):  # pragma: no cover
        raise ZValueError(a=a, b=b)
    if isinstance(b, tuple):  # pragma: no cover
        raise ZValueError(a=a, b=b)
    if a is b or (a == b):
        return a
    if a is object:
        return b
    if b is object:
        return a

    if is_Uninhabited(a):
        return a
    if is_Uninhabited(b):
        return b

    if is_Optional(a):
        if b is type(None):
            return b

    if is_Optional(b):
        if a is type(None):
            return a

    if is_Optional(a) and is_Optional(b):
        x = type_inf(get_Optional_arg(a), get_Optional_arg(b))
        if is_Uninhabited(x):
            return type(None)
        return Optional[x]

    # if not is_Intersection(a) and is_Intersection(b):
    #     r = (a,) + unroll_intersection(b)
    #     return reduce(type_inf, r)

    if is_Intersection(a) or is_Intersection(b):
        ta = unroll_intersection(a)
        tb = unroll_intersection(b)
        tva, oa = get_typevars(ta)
        tvb, ob = get_typevars(tb)
        tv = tuple(set(tva + tvb))
        oab = oa + ob
        if not oab:
            return make_Intersection(tv)
        else:
            other = reduce(type_inf, oa + ob)
            os = unroll_intersection(other)
            return make_Intersection(tv + os)

    if is_Union(b):
        # A ^ (C u D)
        # = A^C u A^D
        r = []
        for t in get_Union_args(b):
            r.append(type_inf(a, t))
        return reduce(type_sup, r)
    # if is_Intersection(a) and  not is_Intersection(b):
    #     res = []
    #     for aa in get_Intersection_args(a):
    #         r = type_inf(aa)
    #     r.extend(unroll_intersection(a))
    #     r.extend(unroll_intersection(b))  # put first!
    #     return reduce(type_inf, r)

    if (a, b) in [(bool, int), (int, bool)]:
        return bool

    if is_TypeVar(a) and is_TypeVar(b):
        if get_TypeVar_name(a) == get_TypeVar_name(b):
            return a

    if is_TypeVar(a) or is_TypeVar(b):
        return make_Intersection((a, b))

    primitive = (bool, int, str, Decimal, datetime, float, bytes, type(None))
    if a in primitive or b in primitive:
        return make_Uninhabited()

    if is_ListLike(a) ^ is_ListLike(b):
        return make_Uninhabited()

    if is_ListLike(a) & is_ListLike(b):
        a = cast(Type[List], a)
        b = cast(Type[List], b)
        A = get_ListLike_arg(a)
        B = get_ListLike_arg(b)
        u = type_inf(A, B)
        return make_list(u)

    if is_SetLike(a) ^ is_SetLike(b):
        return make_Uninhabited()

    if is_SetLike(a) and is_SetLike(b):
        a = cast(Type[Set], a)
        b = cast(Type[Set], b)
        A = get_SetLike_arg(a)
        B = get_SetLike_arg(b)
        u = type_inf(A, B)
        return make_set(u)

    if is_DictLike(a) ^ is_DictLike(b):
        return make_Uninhabited()

    if is_DictLike(a) and is_DictLike(b):
        a = cast(Type[Dict], a)
        b = cast(Type[Dict], b)
        KA, VA = get_DictLike_args(a)
        KB, VB = get_DictLike_args(b)
        K = type_inf(KA, KB)
        V = type_inf(VA, VB)
        return make_dict(K, V)

    if is_dataclass(a) ^ is_dataclass(b):
        return make_Uninhabited()

    if is_dataclass(a) and is_dataclass(b):
        return type_inf_dataclass(a, b)

    if is_VarTuple(a) and is_VarTuple(b):
        a = cast(Type[Tuple], a)
        b = cast(Type[Tuple], b)
        VA = get_VarTuple_arg(a)
        VB = get_VarTuple_arg(b)
        V = type_inf(VA, VB)
        return make_VarTuple(V)

    if is_FixedTupleLike(a) and is_FixedTupleLike(b):
        a = cast(Type[Tuple], a)
        b = cast(Type[Tuple], b)
        tas = get_FixedTupleLike_args(a)
        tbs = get_FixedTupleLike_args(b)
        ts = tuple(type_inf(ta, tb) for ta, tb in zip(tas, tbs))
        return make_Tuple(*ts)

    if is_TypeVar(a) and is_TypeVar(b):
        if get_TypeVar_name(a) == get_TypeVar_name(b):
            return a

    return make_Intersection((a, b))


@dataclass
class MatchConstraint:
    ub: Optional[type] = None
    lb: Optional[type] = None

    def impose_subtype(self, ub) -> "MatchConstraint":
        ub = type_sup(self.ub, ub) if self.ub is not None else ub
        return MatchConstraint(ub=ub, lb=self.lb)

    def impose_supertype(self, lb) -> "MatchConstraint":
        lb = type_inf(self.lb, lb) if self.lb is not None else lb
        return MatchConstraint(lb=lb, ub=self.ub)


DMC = make_dict(str, MatchConstraint)


@dataclass
class Matches:
    m: Dict[str, MatchConstraint] = field(default_factory=DMC)

    def __post_init__(self):
        self.m = DMC(self.m)

    def get_matches(self) -> Dict[str, type]:
        res = DictStrType()
        for k, v in self.m.items():
            if v.ub is not None:
                res[k] = v.ub
        return res

    def get_ub(self, k: str):
        if k not in self.m:
            return None
        return self.m[k].ub

    def get_lb(self, k: str):
        if k not in self.m:
            return None
        return self.m[k].lb

    def must_be_subtype_of(self, k: str, ub) -> "Matches":
        m2 = dict(self.m)
        if k not in m2:
            m2[k] = MatchConstraint()
        m2[k] = m2[k].impose_subtype(ub=ub)
        return Matches(m2)

    def must_be_supertype_of(self, k: str, lb) -> "Matches":
        m2 = dict(self.m)
        if k not in m2:
            m2[k] = MatchConstraint()
        m2[k] = m2[k].impose_supertype(lb=lb)
        return Matches(m2)
