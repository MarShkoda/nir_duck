import datetime
from dataclasses import dataclass, Field, fields, is_dataclass
from typing import cast, Iterator, Optional, Set, TypeVar

import numpy as np
from frozendict import frozendict

from zuper_commons.types import ZNotImplementedError, ZTypeError, ZValueError
from zuper_ipce.types import get_effective_type
from zuper_typing import (DictStrType, get_Optional_arg, get_Union_args, is_Optional,
                          is_SpecialForm,
                          is_Union,
                          lift_to_customtuple, make_dict, same_as_default, value_liskov)
from .constants import (GlobalsDict, HINTS_ATT, IESO, IPCE_PASS_THROUGH, IPCE_TRIVIAL, SCHEMA_ATT)
from .conv_ipce_from_typelike import ipce_from_typelike, ipce_from_typelike_ndarray
from .guesses import (
    get_dict_type_suggestion,
    get_list_type_suggestion,
    get_set_type_suggestion,
    get_tuple_type_suggestion,
)
from .ipce_spec import sorted_dict_cbor_ord
from .structures import FakeValues
from .types import IPCE, is_unconstrained, TypeLike

X = TypeVar("X")


def ipce_from_object(
    ob: object,
    suggest_type: TypeLike = object,
    *,
    globals_: GlobalsDict = None,
    ieso: Optional[IESO] = None,
) -> IPCE:
    # logger.debug(f'ipce_from_object({ob})')
    if ieso is None:
        ieso = IESO(with_schema=True)
    if globals_ is None:
        globals_ = {}
    try:
        res = ipce_from_object_(ob, suggest_type, globals_=globals_, ieso=ieso)
    except TypeError as e:
        msg = "ipce_from_object() for type @t failed."
        raise ZTypeError(msg, ob=ob, T=type(ob)) from e

    # assert_canonical_ipce(res)
    return res


def ipce_from_object_(ob: object, st: TypeLike, *, globals_: GlobalsDict, ieso: IESO) -> IPCE:
    unconstrained = is_unconstrained(st)
    if ob is None:
        if unconstrained or (st is type(None)) or is_Optional(st):
            return ob
        else:  # pragma: no cover
            msg = f"ob is None but suggest_type is @suggest_type"
            raise ZTypeError(msg, suggest_type=st)

    if is_Optional(st):
        assert ob is not None  # from before
        T = get_Optional_arg(st)
        return ipce_from_object_(ob, T, globals_=globals_, ieso=ieso)

    if is_Union(st):
        return ipce_from_object_union(ob, st, globals_=globals_, ieso=ieso)

    if isinstance(ob, datetime.datetime):
        if not ob.tzinfo:
            msg = "Cannot serialize dates without a timezone."
            raise ZValueError(msg, ob=ob)

    if st in IPCE_TRIVIAL:
        if not isinstance(ob, st):
            msg = "Expected this to be @suggest_type."
            raise ZTypeError(msg, st=st, ob=ob, T=type(ob))
        return ob

    if isinstance(ob, IPCE_TRIVIAL):
        return ob

    if isinstance(ob, list):
        return ipce_from_object_list(ob, st, globals_=globals_, ieso=ieso)

    if isinstance(ob, tuple):
        return ipce_from_object_tuple(ob, st, globals_=globals_, ieso=ieso)

    if isinstance(ob, slice):
        return ipce_from_object_slice(ob, ieso=ieso)

    if isinstance(ob, set):
        return ipce_from_object_set(ob, st, globals_=globals_, ieso=ieso)

    if isinstance(ob, (dict, frozendict)):
        return ipce_from_object_dict(ob, st, globals_=globals_, ieso=ieso)

    if isinstance(ob, type):
        return ipce_from_typelike(ob, globals0=globals_, processing={}, ieso=ieso)

    if is_SpecialForm(cast(TypeLike, ob)):
        ob = cast(TypeLike, ob)
        return ipce_from_typelike(ob, globals0=globals_, processing={}, ieso=ieso)

    if isinstance(ob, np.ndarray):
        return ipce_from_object_numpy(ob, ieso=ieso)

    assert not isinstance(ob, type), ob
    if is_dataclass(ob):
        return ipce_from_object_dataclass_instance(ob, globals_=globals_, ieso=ieso)

    msg = "I do not know a way to convert object @ob of type @T."
    raise ZNotImplementedError(msg, ob=ob, T=type(ob))


def ipce_from_object_numpy(ob, *, ieso: IESO) -> IPCE:
    from .numpy_encoding import ipce_from_numpy_array

    res = ipce_from_numpy_array(ob)
    if ieso.with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike_ndarray().schema
    return res


def ipce_from_object_slice(ob, *, ieso: IESO):
    from .conv_ipce_from_typelike import ipce_from_typelike_slice

    res = {"start": ob.start, "step": ob.step, "stop": ob.stop}
    if ieso.with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike_slice(ieso=ieso).schema
    res = sorted_dict_cbor_ord(res)
    return res


def ipce_from_object_union(ob: object, st: TypeLike, *, globals_, ieso: IESO) -> IPCE:
    ts = get_Union_args(st)
    errors = []
    for Ti in ts:
        can = value_liskov(ob, Ti)
        if can:
            return ipce_from_object(ob, Ti, globals_=globals_, ieso=ieso)
        else:
            errors.append(can)

    msg = "Cannot save union."
    raise ZTypeError(msg, suggest_type=st, value=ob, errors=errors)


def ipce_from_object_list(ob, st: TypeLike, *, globals_: dict, ieso: IESO) -> IPCE:
    assert st is not None

    V = get_list_type_suggestion(ob, st)

    def rec(x: X) -> X:
        return ipce_from_object(x, V, globals_=globals_, ieso=ieso)

    return [rec(_) for _ in ob]


def ipce_from_object_tuple(ob: tuple, st: TypeLike, *, globals_, ieso: IESO) -> IPCE:
    ts = get_tuple_type_suggestion(ob, st)

    res = []
    for _, T in zip(ob, ts):
        x = ipce_from_object(_, T, globals_=globals_, ieso=ieso)
        res.append(x)

    return res


@dataclass
class IterAtt:
    attr: str
    T: TypeLike
    value: object


def iterate_resolved_type_values_without_default(x: dataclass) -> Iterator[IterAtt]:
    for f in fields(type(x)):
        assert isinstance(f, Field), list(fields(type(x)))
        k = f.name
        v0 = getattr(x, k)

        if same_as_default(f, v0):
            continue
        k_st = f.type

        yield IterAtt(k, k_st, v0)


def ipce_from_object_dataclass_instance(ob: dataclass, *, globals_, ieso: IESO) -> IPCE:
    globals_ = dict(globals_)
    res = {}
    T0 = type(ob)
    from .conv_ipce_from_typelike import ipce_from_typelike

    if ieso.with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike(T0, globals0=globals_, ieso=ieso)

    globals_[T0.__name__] = T0

    hints = DictStrType()
    attrs = list(iterate_resolved_type_values_without_default(ob))
    if ieso.with_schema:
        for ia in attrs:

            if isinstance(ia.value, tuple) and is_unconstrained(ia.T):
                v2 = lift_to_customtuple(ia.value)
                hints[ia.attr] = type(v2)

            elif isinstance(ia.value, list) and is_unconstrained(ia.T):
                hints[ia.attr] = type(ia.value)

    for ia in attrs:
        k = ia.attr
        v = ia.value
        T = ia.T
        try:

            res[k] = ipce_from_object(v, T, globals_=globals_, ieso=ieso)

            # needs_schema = isinstance(v, (list, tuple))
            # if ieso.with_schema and needs_schema and is_unconstrained(T):
            #     if isinstance(v, tuple):
            #         Ti = make_Tuple(*get_tuple_type_suggestion(v, T))
            #     else:
            #         Ti = type(v)
            #     hints[k] = Ti

        except IPCE_PASS_THROUGH:  # pragma: no cover
            raise
        except BaseException as e:
            msg = (
                f"Could not serialize an object. Problem "
                f"occurred with the attribute {k!r}. It is supposed to be of type @expected."
            )
            raise ZValueError(msg, expected=T, ob=ob) from e
    if hints:
        # logger.info(hints=hints)
        res[HINTS_ATT] = ipce_from_object(hints, ieso=ieso)
    res = sorted_dict_cbor_ord(res)

    return res


def ipce_from_object_dict(ob: dict, st: TypeLike, *, globals_: GlobalsDict, ieso: IESO):
    K, V = get_dict_type_suggestion(ob, st)
    DT = make_dict(K, V)
    res = {}

    from .conv_ipce_from_typelike import ipce_from_typelike

    if ieso.with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike(DT, globals0=globals_, ieso=ieso)

    K = get_effective_type(K)
    if isinstance(K, type) and issubclass(K, str):
        for k, v in ob.items():
            res[k] = ipce_from_object(v, V, globals_=globals_, ieso=ieso)
    elif isinstance(K, type) and issubclass(K, int):
        for k, v in ob.items():
            res[str(k)] = ipce_from_object(v, V, globals_=globals_, ieso=ieso)
    else:
        FV = FakeValues[K, V]
        # group first by the type name, then sort by key
        items = [(type(k).__name__, k, v) for k, v in ob.items()]
        items = sorted(items)
        for i, (_, k, v) in enumerate(items):
            h = get_key_for_set_entry(i, len(ob))
            fv = FV(k, v)
            res[h] = ipce_from_object(fv, globals_=globals_, ieso=ieso)
    res = sorted_dict_cbor_ord(res)
    return res


def ipce_from_object_set(ob: set, st: TypeLike, *, globals_: GlobalsDict, ieso: IESO):
    from .conv_ipce_from_typelike import ipce_from_typelike

    V = get_set_type_suggestion(ob, st)
    ST = Set[V]

    res = {}
    if ieso.with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike(ST, globals0=globals_, ieso=ieso)

    # group first by the type name, then sort by key
    items = [(type(v).__name__, v) for v in ob]
    items = sorted(items)

    for i, (_, v) in enumerate(items):
        vj = ipce_from_object(v, V, globals_=globals_, ieso=ieso)
        h = get_key_for_set_entry(i, len(ob))
        res[h] = vj

    res = sorted_dict_cbor_ord(res)
    return res


def get_key_for_set_entry(i: int, n: int):
    ndigits = len(str(n))
    format0 = f"%0{ndigits}d"
    x = format0 % i
    return f"set:{x}"
