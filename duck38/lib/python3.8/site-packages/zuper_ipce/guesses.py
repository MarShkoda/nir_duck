from typing import cast, Dict, List, Set, Tuple, Type, TypeVar

from zuper_commons.types import ZTypeError, ZValueError
from zuper_typing import (
    CustomDict,
    CustomList,
    CustomSet,
    CustomTuple,
    get_CustomDict_args,
    get_CustomList_arg,
    get_CustomSet_arg,
    get_CustomTuple_args,
    get_DictLike_args,
    get_FixedTupleLike_args,
    get_ListLike_arg,
    get_Optional_arg,
    get_SetLike_arg,
    get_Union_args,
    get_VarTuple_arg,
    is_CustomDict,
    is_CustomList,
    is_CustomSet,
    is_CustomTuple,
    is_DictLike,
    is_FixedTupleLike,
    is_ListLike,
    is_Optional,
    is_SetLike,
    is_Union,
    is_VarTuple,
    TypeLike,
)
from .types import is_unconstrained

X_ = TypeVar("X_")


def get_set_type_suggestion(x: set, st: TypeLike) -> TypeLike:
    T = type(x)
    if is_CustomSet(T):
        T = cast(Type[CustomSet], T)
        return get_CustomSet_arg(T)

    if is_SetLike(st):
        st = cast(Type[Set], st)
        V = get_SetLike_arg(st)
        return V
    elif is_unconstrained(st):
        return object
    else:  # pragma: no cover
        msg = "suggest_type does not make sense for a list"
        raise ZTypeError(msg, suggest_type=st)


def get_list_type_suggestion(x: list, st: TypeLike) -> TypeLike:
    T = type(x)
    if is_CustomList(T):
        T = cast(Type[CustomList], T)
        return get_CustomList_arg(T)

    # TODO: if it is custom dict
    if is_unconstrained(st):
        return object
    elif is_ListLike(st):
        T = cast(Type[List], st)
        V = get_ListLike_arg(T)
        return V
    else:
        msg = "suggest_type does not make sense for a list"
        raise ZTypeError(msg, suggest_type=st, x=type(st))


def get_dict_type_suggestion(ob: dict, st: TypeLike) -> Tuple[type, type]:
    """ Gets the type to use to serialize a dict.
        Returns Dict[K, V], K, V
    """
    T = type(ob)
    if is_CustomDict(T):
        # if it has the type information, then go for it
        T = cast(Type[CustomDict], T)
        K, V = get_CustomDict_args(T)
        return K, V

    if is_DictLike(st):
        # There was a suggestion of Dict-like
        st = cast(Type[Dict], st)
        K, V = get_DictLike_args(st)
        return K, V
    elif is_unconstrained(st):
        # Guess from the dictionary itself
        K, V = guess_type_for_naked_dict(ob)
        return K, V
    else:  # pragma: no cover
        msg = f"@suggest_type does not make sense for a dict"
        raise ZValueError(msg, ob=ob, suggest_type=st)


def is_UnionLike(x: TypeLike) -> bool:
    return is_Union(x) or is_Optional(x)


def get_UnionLike_args(x: TypeLike) -> Tuple[TypeLike, ...]:
    if is_Union(x):
        return get_Union_args(x)
    elif is_Optional(x):
        y = get_Optional_arg(x)
        if is_UnionLike(y):
            return get_UnionLike_args(y) + (type(None),)
        return (y,)
    else:
        assert False


def get_tuple_type_suggestion(x: tuple, st: TypeLike) -> Tuple[TypeLike, ...]:
    if is_UnionLike(st):
        raise ZValueError("Does not support unions here", x=x, st=st)

    # if isinstance(x, CustomTuple):
    #     return type(x).__tuple_types__

    if is_CustomTuple(st):
        st = cast(Type[CustomTuple], st)
        return get_CustomTuple_args(st)

    n = len(x)
    #     options = get_UnionLike_args(st)
    # else:
    # options = (st,)

    # first look for any tufor op in options:
    if is_VarTuple(st):
        st = cast(Type[Tuple[X_, ...]], st)
        V = get_VarTuple_arg(st)
        return tuple([V] * n)
    if is_FixedTupleLike(st):
        st = cast(Type[Tuple], st)
        ts = get_FixedTupleLike_args(st)
        return ts

    if is_unconstrained(st):
        return tuple([object] * n)

    msg = f"@suggest_type does not make sense for a tuple"
    raise ZValueError(msg, suggest_type=st)


def guess_type_for_naked_dict(ob: dict) -> Tuple[type, type]:
    if not ob:
        return object, object
    type_values = tuple(type(_) for _ in ob.values())
    type_keys = tuple(type(_) for _ in ob.keys())

    if len(set(type_keys)) == 1:
        K = type_keys[0]
    else:
        K = object

    if len(set(type_values)) == 1:
        V = type_values[0]
    else:
        V = object
    return K, V
