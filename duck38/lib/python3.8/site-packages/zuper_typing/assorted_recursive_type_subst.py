import datetime
from dataclasses import is_dataclass
from decimal import Decimal
from numbers import Number
from typing import Callable, cast, ClassVar, Dict, List, NewType, Optional, Set, Tuple, Type

import numpy as np

from zuper_commons.types import ZAssertionError
from .aliases import TypeLike
from .annotations_tricks import (
    get_Callable_info,
    get_ClassVar_arg,
    get_Dict_args,
    get_List_arg,
    get_NewType_arg,
    get_NewType_name,
    get_Optional_arg,
    get_Set_arg,
    get_Type_arg,
    get_Union_args,
    get_VarTuple_arg,
    is_Any,
    is_Callable,
    is_ClassVar,
    is_Dict,
    is_ForwardRef,
    is_List,
    is_NewType,
    is_Optional,
    is_Set,
    is_Type,
    is_TypeVar,
    is_Union,
    is_VarTuple,
    make_Tuple,
    make_Union,
)
from .dataclass_info import DataclassInfo, get_dataclass_info, set_dataclass_info
from .monkey_patching_typing import my_dataclass
from .annotations_tricks import (
    CustomDict,
    CustomList,
    CustomSet,
    get_CustomDict_args,
    get_CustomList_arg,
    get_CustomSet_arg,
    is_CustomDict,
    is_CustomList,
    is_CustomSet,
    is_TupleLike,
    make_dict,
    make_list,
    make_set,
    is_FixedTupleLike,
    get_FixedTupleLike_args,
)

__all__ = ["recursive_type_subst", "check_no_placeholders_left"]


def recursive_type_subst(
    T: TypeLike, f: Callable[[TypeLike], TypeLike], ignore: tuple = ()
) -> TypeLike:
    if T in ignore:
        # logger.info(f'ignoring {T} in {ignore}')
        return T
    r = lambda _: recursive_type_subst(_, f, ignore + (T,))
    if is_Optional(T):
        a = get_Optional_arg(T)
        a2 = r(a)
        if a == a2:
            return T
        # logger.info(f'Optional unchanged under {f.__name__}: {a} == {a2}')
        return Optional[a2]
    elif is_ForwardRef(T):
        return f(T)
    elif is_Union(T):
        ts0 = get_Union_args(T)
        ts = tuple(r(_) for _ in ts0)
        if ts0 == ts:
            # logger.info(f'Union unchanged under {f.__name__}: {ts0} == {ts}')
            return T
        return make_Union(*ts)
    elif is_TupleLike(T):
        T = cast(Type[Tuple], T)
        if is_VarTuple(T):
            X = get_VarTuple_arg(T)
            X2 = r(X)
            if X == X2:
                return T
            return Tuple[X2, ...]
        elif is_FixedTupleLike(T):
            argst = get_FixedTupleLike_args(T)
            ts = tuple(r(_) for _ in argst)
            if argst == ts:
                return T
            return make_Tuple(*ts)
        else:
            assert False
    elif is_Dict(T):
        T = cast(Type[Dict], T)
        K, V = get_Dict_args(T)
        K2, V2 = r(K), r(V)
        if (K, V) == (K2, V2):
            return T
        return Dict[K, V]
        # return original_dict_getitem((K, V))
    elif is_CustomDict(T):
        T = cast(Type[CustomDict], T)
        K, V = get_CustomDict_args(T)
        K2, V2 = r(K), r(V)
        if (K, V) == (K2, V2):
            return T
        return make_dict(K2, V2)
    elif is_List(T):
        T = cast(Type[List], T)
        V = get_List_arg(T)
        V2 = r(V)
        if V == V2:
            return T
        return List[V2]

    elif is_CustomList(T):
        T = cast(Type[CustomList], T)
        V = get_CustomList_arg(T)
        V2 = r(V)
        if V == V2:
            return T
        return make_list(V2)
    elif is_Set(T):
        T = cast(Type[Set], T)
        V = get_Set_arg(T)
        V2 = r(V)
        if V == V2:
            return T
        return make_set(V2)
    elif is_CustomSet(T):
        T = cast(Type[CustomSet], T)
        V = get_CustomSet_arg(T)
        V2 = r(V)
        if V == V2:
            return T
        return make_set(V2)
    elif is_NewType(T):
        name = get_NewType_name(T)
        a = get_NewType_arg(T)
        a2 = r(a)
        if a == a2:
            return T

        return NewType(name, a2)
    elif is_ClassVar(T):
        V = get_ClassVar_arg(T)
        V2 = r(V)
        if V == V2:
            return T
        return ClassVar[V2]
    elif is_dataclass(T):
        return recursive_type_subst_dataclass(T, f, ignore)

    elif T in (
        int,
        bool,
        float,
        Decimal,
        datetime.datetime,
        bytes,
        str,
        type(None),
        type,
        np.ndarray,
        Number,
        object,
    ):
        return f(T)
    elif is_TypeVar(T):
        return f(T)
    elif is_Type(T):
        V = get_Type_arg(T)
        V2 = r(V)
        if V == V2:
            return T
        return Type[V2]
    elif is_Any(T):
        return f(T)
    elif is_Callable(T):
        info = get_Callable_info(T)
        args = []
        for k, v in info.parameters_by_name.items():
            # if is_MyNamedArg(v):
            #     # try:
            #     v = v.original
            # TODO: add MyNamedArg
            args.append(f(v))
        fret = f(info.returns)
        args = list(args)
        # noinspection PyTypeHints
        return Callable[args, fret]
        # noinspection PyTypeHints

    elif isinstance(T, type) and "Placeholder" in T.__name__:
        return f(T)
    else:  # pragma: no cover
        # raise ZNotImplementedError(T=T)
        # FIXME
        return T


def recursive_type_subst_dataclass(T, f: Callable[[TypeLike], TypeLike], ignore: tuple = ()):
    def r(_):
        return recursive_type_subst(_, f, ignore + (T,))

    annotations = dict(getattr(T, "__annotations__", {}))
    annotations2 = {}
    nothing_changed = True
    for k, v0 in list(annotations.items()):
        v2 = r(v0)
        nothing_changed &= v0 == v2
        annotations2[k] = v2
    if nothing_changed:
        # logger.info(f'Union unchanged under {f.__name__}: {ts0} == {ts}')
        return T
    from .zeneric2 import GenericProxy

    class Base(GenericProxy):
        pass

    Base.__annotations__ = annotations2
    Base.__module__ = T.__module__
    T2 = my_dataclass(Base)
    for k in annotations:
        if hasattr(T, k):
            setattr(T2, k, getattr(T, k))

    # always
    setattr(T2, "__doc__", getattr(T, "__doc__", None))
    clsi = get_dataclass_info(T)

    # bindings2 = {r(k): r(v) for k, v in clsi.bindings.items()}
    # extra2 = tuple(r(_) for _ in clsi.extra)
    orig2 = tuple(r(_) for _ in clsi.orig)
    clsi2 = DataclassInfo(name="", orig=orig2)
    from .zeneric2 import get_name_for

    name2 = get_name_for(T.__name__, clsi2)
    clsi2.name = name2
    setattr(T2, "__name__", name2)

    qualname = getattr(T, "__qualname__")
    qualname2 = qualname.replace(T.__name__, name2)
    setattr(T2, "__qualname__", qualname2)

    set_dataclass_info(T2, clsi2)

    return T2


def check_no_placeholders_left(T: type):
    """ Check that there is no Placeholder* left in the type. """

    def f(x):
        if isinstance(x, type) and x.__name__.startswith("Placeholder"):
            msg = "Found Placeholder"
            raise ZAssertionError(msg, x=x)
        return x

    return recursive_type_subst(T, f)
