import traceback
from dataclasses import dataclass, is_dataclass
from datetime import datetime
from decimal import Decimal
from typing import cast, Dict, Iterator, List, Optional, Set, Tuple, Type, Union

from zuper_commons.types import ZNotImplementedError, ZValueError
from . import logger
from .aliases import TypeLike
from .annotations_tricks import (
    get_ClassVar_arg,
    get_DictLike_args,
    get_fields_including_static,
    get_FixedTupleLike_args,
    get_ListLike_arg,
    get_NewType_arg,
    get_NewType_name,
    get_Optional_arg,
    get_SetLike_arg,
    get_Type_arg,
    get_TypeVar_name,
    get_Union_args,
    get_VarTuple_arg,
    is_Any,
    is_ClassVar,
    is_DictLike,
    is_FixedTupleLike,
    is_ListLike,
    is_NewType,
    is_Optional,
    is_SetLike,
    is_Type,
    is_TypeLike,
    is_TypeVar,
    is_Union,
    is_VarTuple,
    MyBytes,
    MyStr,
)
from .dataclass_info import get_fields_values, is_dataclass_instance
from .literal import get_Literal_args, is_Literal
from .my_intersection import get_Intersection_args, is_Intersection
from .uninhabited import is_Uninhabited

assert logger

__all__ = [
    "assert_equivalent_objects",
    "assert_equivalent_types",
    "get_patches",
    "is_placeholder",
    "patch",
    "NotEquivalentException",
]


@dataclass
class Patch:
    __print_order__ = ["prefix_str", "value1", "value2", "msg"]
    prefix: Tuple[Union[str, int], ...]
    value1: object
    value2: Optional[object]
    prefix_str: Optional[str] = None
    msg: Optional[str] = None

    def __post_init__(self):
        self.prefix_str = "/".join(map(str, self.prefix))


def assert_equivalent_objects(ob1: object, ob2: object, compare_types: bool = True):
    if is_TypeLike(ob1):
        ob1 = cast(TypeLike, ob1)
        ob2 = cast(TypeLike, ob2)
        assert_equivalent_types(ob1, ob2)
    else:
        patches = get_patches(ob1, ob2, compare_types)
        if patches:
            msg = "The objects are not equivalent"
            raise ZValueError(msg, ob1=ob1, ob2=ob2, patches=patches)


def get_patches(a: object, b: object, compare_types: bool = True) -> List[Patch]:
    patches = list(patch(a, b, (), compare_types))
    return patches


def patch(
    o1, o2, prefix: Tuple[Union[str, int], ...], compare_types: bool = True
) -> Iterator[Patch]:
    import numpy as np

    if isinstance(o1, np.ndarray):
        if np.all(o1 == o2):
            return
        else:
            yield Patch(prefix, o1, o2)
    if o1 == o2:
        return
    if is_TypeLike(o1) and is_TypeLike(o2):
        try:
            assert_equivalent_types(o1, o2)
        except NotEquivalentException as e:
            yield Patch(prefix, o1, o2, msg=traceback.format_exc())

    elif is_dataclass_instance(o1) and is_dataclass_instance(o2):
        if compare_types:
            try:
                assert_equivalent_types(type(o1), type(o2))
            except BaseException as e:
                yield Patch(
                    prefix=prefix + ("$schema",),
                    value1=type(o1),
                    value2=type(o2),
                    msg=traceback.format_exc(),
                )
        fields1 = get_fields_values(o1)
        fields2 = get_fields_values(o2)
        if list(fields1) != list(fields2):
            yield Patch(prefix, o1, o2)
        for k in fields1:
            v1 = fields1[k]
            v2 = fields2[k]
            yield from patch(v1, v2, prefix + (k,), compare_types)
    elif isinstance(o1, dict) and isinstance(o2, dict):
        for k, v in o1.items():
            if not k in o2:
                yield Patch(prefix + (k,), v, None)
            else:
                yield from patch(v, o2[k], prefix + (k,), compare_types)
    elif isinstance(o1, list) and isinstance(o2, list):
        n = max(len(o1), len(o2))
        for i in range(n):
            if i >= len(o1):
                yield Patch(prefix + (i,), value1=o1, value2=o2, msg="Different length")
            elif i >= len(o2):
                yield Patch(prefix + (i,), value1=o1, value2=o2, msg="Different length")
            else:
                yield from patch(o1[i], o2[i], prefix + (i,), compare_types)
        # todo: we also need to check
    else:
        if o1 != o2:
            yield Patch(prefix, o1, o2)


class NotEquivalentException(ZValueError):
    pass


from .zeneric2 import DataclassInfo


def check_dataclass_info_same(d1, d2, assume_yes: Set[Tuple[int, int]]):

    d1 = cast(DataclassInfo, d1)
    d2 = cast(DataclassInfo, d2)

    if len(d1.orig) != len(d2.orig):
        msg = "Different orig"
        raise NotEquivalentException(msg, d1=d1, d2=d2)

    for t1, t2 in zip(d1.orig, d2.orig):
        assert_equivalent_types(t1, t2, assume_yes=assume_yes)


def sort_dict(x: dict) -> dict:
    keys = list(x)
    keys_sorted = sorted(keys, key=lambda _: repr(_))
    return {k: x[k] for k in keys_sorted}


def is_placeholder(x):
    return hasattr(x, "__name__") and "Placeholder" in x.__name__


def strip_my_types(T: TypeLike):
    if T is MyBytes:
        return bytes
    if T is MyStr:
        return str
    return T


from .zeneric2 import get_dataclass_info


def assert_equivalent_types(
    T1: TypeLike, T2: TypeLike, assume_yes: set = None, bypass_identity=False
):
    T1 = strip_my_types(T1)
    T2 = strip_my_types(T2)

    if assume_yes is None:
        # logger.warn('assuming yes from scratch')
        assume_yes = set()
    # debug(f'equivalent', T1=T1, T2=T2)
    key = (id(T1), id(T2))
    if key in assume_yes:
        return

    if is_placeholder(T1) or is_placeholder(T2):
        msg = "One class is incomplete"
        raise NotEquivalentException(msg, T1=T1, T2=T2)

    assume_yes = set(assume_yes)
    assume_yes.add(key)

    recursive = lambda t1, t2: assert_equivalent_types(
        T1=t1, T2=t2, assume_yes=assume_yes, bypass_identity=bypass_identity
    )
    try:
        # print(f'assert_equivalent_types({T1},{T2})')
        if (T1 is T2) and (not is_dataclass(T1) or bypass_identity):
            # logger.debug('same by equality')
            return

        if is_dataclass(T1):
            if not is_dataclass(T2):
                raise NotEquivalentException(T1=T1, T2=T2)

            # warnings.warn("devl")
            if False:
                if type(T1) != type(T2):
                    msg = f"Different types for types: {type(T1)} {type(T2)}"
                    raise NotEquivalentException(msg, T1=T1, T2=T2)

            atts = ["__name__", "__module__"]

            # atts.append('__doc__')
            if "__doc__" not in atts:
                pass
                # warnings.warn("de-selected __doc__ comparison")
            for k in atts:

                v1 = getattr(T1, k, ())
                v2 = getattr(T2, k, ())
                if v1 != v2:
                    msg = f"Difference for {k} of {T1} ({type(T1)}) and {T2} ({type(T2)}"
                    raise NotEquivalentException(msg, v1=v1, v2=v2)

            T1i = get_dataclass_info(T1)
            T2i = get_dataclass_info(T2)
            check_dataclass_info_same(T1i, T2i, assume_yes)
            fields1 = get_fields_including_static(T1)
            fields2 = get_fields_including_static(T2)
            if list(fields1) != list(fields2):
                msg = f"Different fields"
                raise NotEquivalentException(msg, fields1=fields1, fields2=fields2)

            ann1 = getattr(T1, "__annotations__", {})
            ann2 = getattr(T2, "__annotations__", {})

            for k in fields1:
                t1 = fields1[k].type
                t2 = fields2[k].type

                try:
                    recursive(t1, t2)
                except NotEquivalentException as e:
                    msg = f"Could not establish the annotation {k!r} to be equivalent"
                    raise NotEquivalentException(
                        msg,
                        t1=t1,
                        t2=t2,
                        t1_ann=T1.__annotations__[k],
                        t2_ann=T2.__annotations__[k],
                        t1_att=getattr(T1, k, "no attribute"),
                        t2_att=getattr(T2, k, "no attribute"),
                    ) from e

                d1 = fields1[k].default
                d2 = fields2[k].default
                try:
                    assert_equivalent_objects(d1, d2)
                except ZValueError as e:
                    raise NotEquivalentException(d1=d1, d2=d2) from e
                # if d1 != d2:
                #     msg = f"Defaults for {k!r} are different."
                #     raise NotEquivalentException(msg, d1=d1, d2=d2)
                #
                # d1 = fields1[k].default_factory
                # d2 = fields2[k].default
                # if d1 != d2:
                #     msg = f"Defaults for {k!r} are different."
                #     raise NotEquivalentException(msg, d1=d1, d2=d2)

            for k in ann1:
                t1 = ann1[k]
                t2 = ann2[k]
                try:
                    recursive(t1, t2)
                except NotEquivalentException as e:
                    msg = f"Could not establish the annotation {k!r} to be equivalent"
                    raise NotEquivalentException(
                        msg,
                        t1=t1,
                        t2=t2,
                        t1_ann=T1.__annotations__[k],
                        t2_ann=T2.__annotations__[k],
                        t1_att=getattr(T1, k, "no attribute"),
                        t2_att=getattr(T2, k, "no attribute"),
                    ) from e

        elif is_Literal(T1):
            if not is_Literal(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            values1 = get_Literal_args(T1)
            values2 = get_Literal_args(T2)
            if values1 != values2:
                raise NotEquivalentException(T1=T1, T2=T2)
        elif is_ClassVar(T1):
            if not is_ClassVar(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            t1 = get_ClassVar_arg(T1)
            t2 = get_ClassVar_arg(T2)
            recursive(t1, t2)
        elif is_Optional(T1):
            if not is_Optional(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            t1 = get_Optional_arg(T1)
            t2 = get_Optional_arg(T2)
            recursive(t1, t2)
        elif T1 is type(None):
            if not T2 is type(None):
                raise NotEquivalentException(T1=T1, T2=T2)

        elif is_Union(T1):
            if not is_Union(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            ts1 = get_Union_args(T1)
            ts2 = get_Union_args(T2)
            for t1, t2 in zip(ts1, ts2):
                recursive(t1, t2)
        elif is_Intersection(T1):
            if not is_Intersection(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            ts1 = get_Intersection_args(T1)
            ts2 = get_Intersection_args(T2)
            for t1, t2 in zip(ts1, ts2):
                recursive(t1, t2)
        elif is_FixedTupleLike(T1):
            if not is_FixedTupleLike(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            T1 = cast(Type[Tuple], T1)
            T2 = cast(Type[Tuple], T2)
            ts1 = get_FixedTupleLike_args(T1)
            ts2 = get_FixedTupleLike_args(T2)
            for t1, t2 in zip(ts1, ts2):
                recursive(t1, t2)
        elif is_VarTuple(T1):
            if not is_VarTuple(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            T1 = cast(Type[Tuple], T1)
            T2 = cast(Type[Tuple], T2)
            t1 = get_VarTuple_arg(T1)
            t2 = get_VarTuple_arg(T2)
            recursive(t1, t2)
        elif is_SetLike(T1):
            T1 = cast(Type[Set], T1)
            if not is_SetLike(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            T2 = cast(Type[Set], T2)
            t1 = get_SetLike_arg(T1)
            t2 = get_SetLike_arg(T2)
            recursive(t1, t2)
        elif is_ListLike(T1):
            T1 = cast(Type[List], T1)
            if not is_ListLike(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            T2 = cast(Type[List], T2)
            t1 = get_ListLike_arg(T1)
            t2 = get_ListLike_arg(T2)
            recursive(t1, t2)
        elif is_DictLike(T1):
            T1 = cast(Type[Dict], T1)
            if not is_DictLike(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            T2 = cast(Type[Dict], T2)
            t1, u1 = get_DictLike_args(T1)
            t2, u2 = get_DictLike_args(T2)
            recursive(t1, t2)
            recursive(u1, u2)

        elif is_Any(T1):
            if not is_Any(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
        elif is_TypeVar(T1):
            if not is_TypeVar(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            n1 = get_TypeVar_name(T1)
            n2 = get_TypeVar_name(T2)
            if n1 != n2:
                raise NotEquivalentException(n1=n1, n2=n2)
        elif T1 in (int, str, bool, Decimal, datetime, float, type):
            if T1 != T2:
                raise NotEquivalentException(T1=T1, T2=T2)
        elif is_NewType(T1):
            if not is_NewType(T2):
                raise NotEquivalentException(T1=T1, T2=T2)

            n1 = get_NewType_name(T1)
            n2 = get_NewType_name(T2)
            if n1 != n2:
                raise NotEquivalentException(T1=T1, T2=T2)

            o1 = get_NewType_arg(T1)
            o2 = get_NewType_arg(T2)
            recursive(o1, o2)
        elif is_Type(T1):
            if not is_Type(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            t1 = get_Type_arg(T1)
            t2 = get_Type_arg(T2)
            recursive(t1, t2)
        elif is_Uninhabited(T1):
            if not is_Uninhabited(T2):
                raise NotEquivalentException(T1=T1, T2=T2)

        else:
            raise ZNotImplementedError(T1=T1, T2=T2)

    except NotEquivalentException as e:
        # logger.error(e)
        msg = f"Could not establish the two types to be equivalent."
        raise NotEquivalentException(msg, T1=T1, T2=T2) from e
    # assert T1 == T2
    # assert_equal(T1.mro(), T2.mro())
