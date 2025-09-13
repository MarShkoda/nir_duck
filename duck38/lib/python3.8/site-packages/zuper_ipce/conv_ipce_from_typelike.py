import copy
import dataclasses
import datetime
import warnings
from dataclasses import Field, is_dataclass, replace
from decimal import Decimal
from numbers import Number
from typing import (
    cast,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
)

import numpy as np

from zuper_commons.types import (
    ZAssertionError,
    ZTypeError,
    ZValueError,
)
from zuper_ipce.types import get_effective_type
from zuper_typing import (
    dataclass,
    get_Callable_info,
    get_ClassVar_arg,
    get_dataclass_info,
    get_Dict_name_K_V,
    get_DictLike_args,
    get_fields_including_static,
    get_FixedTupleLike_args,
    get_FixedTupleLike_name,
    get_ForwardRef_arg,
    get_Intersection_args,
    get_ListLike_arg,
    get_ListLike_name,
    get_Literal_args,
    get_name_without_brackets,
    get_NewType_arg,
    get_NewType_name,
    get_Optional_arg,
    get_Sequence_arg,
    get_Set_name_V,
    get_SetLike_arg,
    get_Tuple_name,
    get_Type_arg,
    get_TypeVar_bound,
    get_TypeVar_name,
    get_Union_args,
    get_VarTuple_arg,
    is_Any,
    is_Callable,
    is_ClassVar,
    is_FixedTupleLike,
    is_ForwardRef,
    is_DictLike,
    is_Intersection,
    is_ListLike,
    is_Literal,
    is_NewType,
    is_Optional,
    is_Sequence,
    is_SetLike,
    is_TupleLike,
    is_Type,
    is_TypeLike,
    is_TypeVar,
    is_Union,
    is_VarTuple,
    key_for_sorting_types,
    MyBytes,
    MyStr,
    TypeLike,
)
from .constants import (
    ALL_OF,
    ANY_OF,
    ATT_PYTHON_NAME,
    CALLABLE_ORDERING,
    CALLABLE_RETURN,
    ID_ATT,
    IESO,
    IPCE_PASS_THROUGH,
    JSC_ADDITIONAL_PROPERTIES,
    JSC_ARRAY,
    JSC_BOOL,
    JSC_DEFINITIONS,
    JSC_DESCRIPTION,
    JSC_INTEGER,
    JSC_ITEMS,
    JSC_NULL,
    JSC_NUMBER,
    JSC_OBJECT,
    JSC_PROPERTIES,
    JSC_PROPERTY_NAMES,
    JSC_REQUIRED,
    JSC_STRING,
    JSC_TITLE,
    JSC_TITLE_CALLABLE,
    JSC_TITLE_DATETIME,
    JSC_TITLE_DECIMAL,
    JSC_TITLE_FLOAT,
    JSC_TITLE_NUMPY,
    JSC_TITLE_SLICE,
    JSC_TITLE_TYPE,
    JSC_TYPE,
    JSONSchema,
    ProcessingDict,
    REF_ATT,
    SCHEMA_ATT,
    SCHEMA_BYTES,
    SCHEMA_CID,
    SCHEMA_ID,
    X_CLASSATTS,
    X_CLASSVARS,
    X_ORDER,
    X_ORIG,
    X_PYTHON_MODULE_ATT,
)
from .ipce_spec import assert_canonical_ipce, sorted_dict_cbor_ord
from .schema_caching import (
    get_ipce_from_typelike_cache,
    set_ipce_from_typelike_cache,
    TRE,
)
from .schema_utils import make_ref, make_url
from .structures import FakeValues
from .types import IPCE


def is_placeholder(x):
    return hasattr(x, "__name__") and "Placeholder" in x.__name__


def ipce_from_typelike(
    T: TypeLike,
    *,
    globals0: Optional[dict] = None,
    processing: Optional[ProcessingDict] = None,
    ieso: Optional[IESO] = None,
) -> JSONSchema:
    if ieso is None:
        ieso = IESO(with_schema=True)
    if processing is None:
        processing = {}
    if globals0 is None:
        globals0 = {}
    c = IFTContext(globals0, processing, ())
    tr = ipce_from_typelike_tr(T, c, ieso=ieso)
    schema = tr.schema
    assert_canonical_ipce(schema)
    return schema


@dataclass
class IFTContext:
    globals_: dict
    processing: ProcessingDict
    context: Tuple[str, ...]


def ipce_from_typelike_tr(T: TypeLike, c: IFTContext, ieso: IESO) -> TRE:
    if is_placeholder(T):
        raise ZValueError(T=T)
    if not is_TypeLike(T):
        raise ValueError(T)

    if hasattr(T, "__name__"):
        if T.__name__ in c.processing:
            ref = c.processing[T.__name__]
            res = make_ref(ref)
            return TRE(res, {T.__name__: ref})

        if ieso.use_ipce_from_typelike_cache:
            try:
                return get_ipce_from_typelike_cache(T, c.processing)
            except KeyError:
                pass

    try:

        if T is type:
            res = cast(
                JSONSchema,
                {
                    REF_ATT: SCHEMA_ID,
                    JSC_TITLE: JSC_TITLE_TYPE
                    # JSC_DESCRIPTION: T.__doc__
                },
            )
            res = sorted_dict_cbor_ord(res)
            return TRE(res)

        if T is type(None):
            res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID, JSC_TYPE: JSC_NULL})
            res = sorted_dict_cbor_ord(res)
            return TRE(res)

        if isinstance(T, type):
            for klass in T.mro():
                if klass.__name__.startswith("Generic"):
                    continue
                if klass is object:
                    continue

                globals2 = dict(c.globals_)
                globals2[get_name_without_brackets(klass.__name__)] = klass

                # clsi = get_dataclass_info(klass)
                # bindings = getattr(klass, BINDINGS_ATT, {})
                # for k, v in clsi.bindings.items():
                #     if hasattr(v, "__name__") and v.__name__ not in globals2:
                #         globals2[v.__name__] = v
                #     globals2[k.__name__] = v

                c = dataclasses.replace(c, globals_=globals2)

        tr: TRE = ipce_from_typelike_tr_(T, c=c, ieso=ieso)

        if ieso.use_ipce_from_typelike_cache:
            set_ipce_from_typelike_cache(T, tr.used, tr.schema)

        return tr
    except IPCE_PASS_THROUGH:  # pragma: no cover
        raise
    except ValueError as e:
        msg = "Cannot get schema for type @T"
        raise ZValueError(msg, T=T, T_type=type(T), c=c) from e
    except AssertionError as e:
        msg = "Cannot get schema for type @T"
        raise ZAssertionError(msg, T=T, T_type=type(T), c=c) from e
    except BaseException as e:
        msg = "Cannot get schema for @T"
        raise ZTypeError(msg, T=T, c=c) from e


def ipce_from_typelike_DictLike(T: Type[Dict], c: IFTContext, ieso: IESO) -> TRE:
    assert is_DictLike(T), T
    K, V = get_DictLike_args(T)
    res = cast(JSONSchema, {JSC_TYPE: JSC_OBJECT})
    res[JSC_TITLE] = get_Dict_name_K_V(K, V)
    K = get_effective_type(K)
    if isinstance(K, type) and issubclass(K, str):
        res[JSC_PROPERTIES] = {SCHEMA_ATT: {}}  # XXX
        tr = ipce_from_typelike_tr(V, c=c, ieso=ieso)
        res[JSC_ADDITIONAL_PROPERTIES] = tr.schema
        res[SCHEMA_ATT] = SCHEMA_ID
        res = sorted_dict_cbor_ord(res)
        return TRE(res, tr.used)
    else:
        res[JSC_PROPERTIES] = {SCHEMA_ATT: {}}  # XXX
        props = FakeValues[K, V]
        tr = ipce_from_typelike_tr(props, c=c, ieso=ieso)
        # logger.warning(f'props IPCE:\n\n {yaml.dump(tr.schema)}')

        res[JSC_ADDITIONAL_PROPERTIES] = tr.schema
        res[SCHEMA_ATT] = SCHEMA_ID
        res = sorted_dict_cbor_ord(res)
        return TRE(res, tr.used)


def ipce_from_typelike_SetLike(T: Type[Set], c: IFTContext, ieso: IESO) -> TRE:
    assert is_SetLike(T), T
    V = get_SetLike_arg(T)
    res = cast(JSONSchema, {JSC_TYPE: JSC_OBJECT})
    res[JSC_TITLE] = get_Set_name_V(V)
    res[JSC_PROPERTY_NAMES] = SCHEMA_CID
    tr = ipce_from_typelike_tr(V, c=c, ieso=ieso)
    res[JSC_ADDITIONAL_PROPERTIES] = tr.schema
    res[SCHEMA_ATT] = SCHEMA_ID
    res = sorted_dict_cbor_ord(res)
    return TRE(res, tr.used)


def ipce_from_typelike_TupleLike(T: TypeLike, c: IFTContext, ieso: IESO) -> TRE:
    assert is_TupleLike(T), T

    used = {}

    def f(x: TypeLike) -> JSONSchema:
        tr = ipce_from_typelike_tr(x, c=c, ieso=ieso)
        used.update(tr.used)
        return tr.schema

    if is_VarTuple(T):
        T = cast(Type[Tuple], T)
        items = get_VarTuple_arg(T)
        res = cast(JSONSchema, {})
        res[SCHEMA_ATT] = SCHEMA_ID
        res[JSC_TYPE] = JSC_ARRAY
        res[JSC_ITEMS] = f(items)
        res[JSC_TITLE] = get_Tuple_name(T)
        res = sorted_dict_cbor_ord(res)
        return TRE(res, used)
    elif is_FixedTupleLike(T):
        T = cast(Type[Tuple], T)
        args = get_FixedTupleLike_args(T)
        res = cast(JSONSchema, {})
        res[SCHEMA_ATT] = SCHEMA_ID
        res[JSC_TYPE] = JSC_ARRAY
        res[JSC_ITEMS] = []
        res[JSC_TITLE] = get_FixedTupleLike_name(T)
        for a in args:
            res[JSC_ITEMS].append(f(a))
        res = sorted_dict_cbor_ord(res)
        return TRE(res, used)
    else:
        assert False


class KeepTrackSer:
    def __init__(self, c: IFTContext, ieso: IESO):
        self.c = c
        self.ieso = ieso
        self.used = {}

    def ipce_from_typelike(self, T: TypeLike) -> JSONSchema:
        tre = ipce_from_typelike_tr(T, c=self.c, ieso=self.ieso)
        self.used.update(tre.used)
        return tre.schema

    # def ipce_from_object(self, x: IPCE, st: TypeLike) -> IPCE:
    #     from .conv_ipce_from_object import ipce_from_object_
    #     res = object_from_ipce_(x, st, ieds=self.ieds, iedo=self.iedo)
    #     return res

    def tre(self, x: IPCE) -> TRE:
        return TRE(x, self.used)


def ipce_from_typelike_NewType(T: TypeLike, c: IFTContext, ieso: IESO) -> TRE:
    _ = c, ieso
    name = get_NewType_name(T)
    T0 = get_NewType_arg(T)
    kt = KeepTrackSer(c, ieso)
    res = cast(JSONSchema, {})
    res[SCHEMA_ATT] = SCHEMA_ID
    res[JSC_TYPE] = "NewType"
    res["newtype"] = kt.ipce_from_typelike(T0)
    res[JSC_TITLE] = name
    res = sorted_dict_cbor_ord(res)
    return kt.tre(res)


def ipce_from_typelike_ListLike(T: Type[List], c: IFTContext, ieso: IESO) -> TRE:
    assert is_ListLike(T), T
    items = get_ListLike_arg(T)
    res = cast(JSONSchema, {})
    kt = KeepTrackSer(c, ieso)

    res[SCHEMA_ATT] = SCHEMA_ID
    res[JSC_TYPE] = JSC_ARRAY
    res[JSC_ITEMS] = kt.ipce_from_typelike(items)
    res[JSC_TITLE] = get_ListLike_name(T)
    res = sorted_dict_cbor_ord(res)
    return kt.tre(res)


def ipce_from_typelike_Callable(T: TypeLike, c: IFTContext, ieso: IESO) -> TRE:
    assert is_Callable(T), T
    cinfo = get_Callable_info(T)

    kt = KeepTrackSer(c, ieso)

    res = cast(
        JSONSchema,
        {
            JSC_TYPE: JSC_OBJECT,
            SCHEMA_ATT: SCHEMA_ID,
            JSC_TITLE: JSC_TITLE_CALLABLE,
            "special": "callable",
        },
    )

    p = res[JSC_DEFINITIONS] = {}

    for k, v in cinfo.parameters_by_name.items():
        p[k] = kt.ipce_from_typelike(v)
    p[CALLABLE_RETURN] = kt.ipce_from_typelike(cinfo.returns)
    res[CALLABLE_ORDERING] = list(cinfo.ordering)
    # print(res)
    res = sorted_dict_cbor_ord(res)
    return kt.tre(res)


def ipce_from_typelike_tr_(T: TypeLike, c: IFTContext, ieso: IESO) -> TRE:
    if T is None:
        msg = "None is not a type!"
        raise ZValueError(msg)

    # This can actually happen inside a Tuple (or Dict, etc.) even though
    # we have a special case for dataclass

    if is_ForwardRef(T):  # pragma: no cover
        msg = "It is not supported to have an ForwardRef here yet."
        raise ZValueError(msg, T=T)

    if isinstance(T, str):  # pragma: no cover
        msg = "It is not supported to have a string here."
        raise ZValueError(msg, T=T)

    if T is str or T is MyStr:
        res = cast(JSONSchema, {JSC_TYPE: JSC_STRING, SCHEMA_ATT: SCHEMA_ID})
        res = sorted_dict_cbor_ord(res)
        return TRE(res)

    if T is bool:
        res = cast(JSONSchema, {JSC_TYPE: JSC_BOOL, SCHEMA_ATT: SCHEMA_ID})
        res = sorted_dict_cbor_ord(res)
        return TRE(res)

    if T is Number:
        res = cast(JSONSchema, {JSC_TYPE: JSC_NUMBER, SCHEMA_ATT: SCHEMA_ID})
        res = sorted_dict_cbor_ord(res)
        return TRE(res)

    if T is float:
        res = {JSC_TYPE: JSC_NUMBER, SCHEMA_ATT: SCHEMA_ID, JSC_TITLE: JSC_TITLE_FLOAT}
        res = cast(JSONSchema, res,)
        res = sorted_dict_cbor_ord(res)
        return TRE(res)

    if T is int:
        res = cast(JSONSchema, {JSC_TYPE: JSC_INTEGER, SCHEMA_ATT: SCHEMA_ID})
        res = sorted_dict_cbor_ord(res)
        return TRE(res)

    if T is slice:
        return ipce_from_typelike_slice(ieso=ieso)

    if T is Decimal:
        res = {JSC_TYPE: JSC_STRING, JSC_TITLE: JSC_TITLE_DECIMAL, SCHEMA_ATT: SCHEMA_ID}
        res = cast(JSONSchema, res,)
        res = sorted_dict_cbor_ord(res)
        return TRE(res)

    if T is datetime.datetime:
        res = {
            JSC_TYPE: JSC_STRING,
            JSC_TITLE: JSC_TITLE_DATETIME,
            SCHEMA_ATT: SCHEMA_ID,
        }
        res = cast(JSONSchema, res)
        res = sorted_dict_cbor_ord(res)
        return TRE(res)

    if T is bytes or T is MyBytes:
        res = SCHEMA_BYTES
        res = sorted_dict_cbor_ord(res)
        return TRE(res)

    if T is object:
        res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID, JSC_TITLE: "object"})
        res = sorted_dict_cbor_ord(res)
        return TRE(res)

    # we cannot use isinstance on typing.Any
    if is_Any(T):  # XXX not possible...
        res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID, JSC_TITLE: "Any"})
        res = sorted_dict_cbor_ord(res)
        return TRE(res)

    if is_Union(T):
        return ipce_from_typelike_Union(T, c=c, ieso=ieso)

    if is_Optional(T):
        return ipce_from_typelike_Optional(T, c=c, ieso=ieso)

    if is_DictLike(T):
        T = cast(Type[Dict], T)
        return ipce_from_typelike_DictLike(T, c=c, ieso=ieso)

    if is_SetLike(T):
        T = cast(Type[Set], T)
        return ipce_from_typelike_SetLike(T, c=c, ieso=ieso)

    if is_Intersection(T):
        return ipce_from_typelike_Intersection(T, c=c, ieso=ieso)

    if is_Callable(T):
        return ipce_from_typelike_Callable(T, c=c, ieso=ieso)

    if is_NewType(T):
        return ipce_from_typelike_NewType(T, c=c, ieso=ieso)

    if is_Sequence(T):
        msg = "Translating Sequence into List"
        warnings.warn(msg)
        T = cast(Type[Sequence], T)
        # raise ValueError(msg)
        V = get_Sequence_arg(T)
        T = List[V]
        return ipce_from_typelike_ListLike(T, c=c, ieso=ieso)

    if is_ListLike(T):
        T = cast(Type[List], T)
        return ipce_from_typelike_ListLike(T, c=c, ieso=ieso)

    if is_TupleLike(T):
        # noinspection PyTypeChecker
        return ipce_from_typelike_TupleLike(T, c=c, ieso=ieso)

    if is_Type(T):
        TT = get_Type_arg(T)
        r = ipce_from_typelike_tr(TT, c, ieso=ieso)
        res = {SCHEMA_ATT: SCHEMA_ID, JSC_TYPE: "subtype", "subtype": r.schema}
        res = cast(JSONSchema, res)
        res = sorted_dict_cbor_ord(res)
        return TRE(res, r.used)
        # raise NotImplementedError(T)

    if is_Literal(T):
        values = get_Literal_args(T)
        T0 = type(values[0])
        r = ipce_from_typelike_tr(T0, c, ieso=ieso)
        from .conv_ipce_from_object import ipce_from_object  # ok-ish

        enum = [ipce_from_object(_, T0) for _ in values]
        res = cast(JSONSchema, dict(r.schema))
        res["enum"] = enum
        res = sorted_dict_cbor_ord(res)
        return TRE(res, r.used)

    assert isinstance(T, type), (T, type(T), is_Optional(T), is_Union(T), is_Literal(T))

    if is_dataclass(T):
        return ipce_from_typelike_dataclass(T, c=c, ieso=ieso)

    if T is np.ndarray:
        return ipce_from_typelike_ndarray()

    msg = "Cannot interpret the type @T"
    raise ZValueError(msg, T=T, c=c)


def ipce_from_typelike_ndarray() -> TRE:
    res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID})
    res[JSC_TYPE] = JSC_OBJECT
    res[JSC_TITLE] = JSC_TITLE_NUMPY
    properties = {"shape": {}, "dtype": {}, "data": SCHEMA_BYTES}  # TODO  # TODO
    properties = sorted_dict_cbor_ord(properties)
    res[JSC_PROPERTIES] = properties
    res = sorted_dict_cbor_ord(res)
    return TRE(res)


def ipce_from_typelike_slice(ieso: IESO) -> TRE:
    res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID})
    res[JSC_TYPE] = JSC_OBJECT
    res[JSC_TITLE] = JSC_TITLE_SLICE
    c = IFTContext({}, {}, ())
    tr = ipce_from_typelike_tr(Optional[int], c=c, ieso=ieso)
    properties = {
        "start": tr.schema,  # TODO
        "stop": tr.schema,  # TODO
        "step": tr.schema,
    }
    res[JSC_PROPERTIES] = sorted_dict_cbor_ord(properties)
    res = sorted_dict_cbor_ord(res)
    return TRE(res, tr.used)


def ipce_from_typelike_Intersection(T: TypeLike, c: IFTContext, ieso: IESO):
    args = get_Intersection_args(T)
    kt = KeepTrackSer(c, ieso)

    options = [kt.ipce_from_typelike(t) for t in args]
    res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID, ALL_OF: options})
    res = sorted_dict_cbor_ord(res)
    return kt.tre(res)


def get_mentioned_names(T: TypeLike, context=()) -> Iterator[str]:
    if T in context:
        return
    c2 = context + (T,)
    if is_dataclass(T):
        if context:
            yield T.__name__
        annotations = getattr(T, "__annotations__", {})
        for v in annotations.values():
            yield from get_mentioned_names(v, c2)
    elif is_Type(T):
        v = get_Type_arg(T)
        yield from get_mentioned_names(v, c2)
    elif is_TypeVar(T):
        yield get_TypeVar_name(T)

    elif is_FixedTupleLike(T):
        T = cast(Type[Tuple], T)
        for t in get_FixedTupleLike_args(T):
            yield from get_mentioned_names(t, c2)
    elif is_VarTuple(T):
        T = cast(Type[Tuple], T)
        t = get_VarTuple_arg(T)
        yield from get_mentioned_names(t, c2)
    elif is_ListLike(T):
        T = cast(Type[List], T)
        t = get_ListLike_arg(T)
        yield from get_mentioned_names(t, c2)

    elif is_DictLike(T):
        T = cast(Type[Dict], T)
        K, V = get_DictLike_args(T)
        yield from get_mentioned_names(K, c2)
        yield from get_mentioned_names(V, c2)
    elif is_SetLike(T):
        T = cast(Type[Set], T)
        t = get_SetLike_arg(T)
        yield from get_mentioned_names(t, c2)

    elif is_ForwardRef(T):
        return get_ForwardRef_arg(T)

    elif is_Optional(T):

        t = get_Optional_arg(T)
        yield from get_mentioned_names(t, c2)

    elif is_Union(T):
        for t in get_Union_args(T):
            yield from get_mentioned_names(t, c2)
    else:
        pass


def ipce_from_typelike_dataclass(T: TypeLike, c: IFTContext, ieso: IESO) -> TRE:
    assert is_dataclass(T), T

    # noinspection PyDataclass
    c = replace(
        c,
        globals_=dict(c.globals_),
        processing=dict(c.processing),
        context=c.context + (T.__name__,),
    )

    used = {}

    def ftl(x: TypeLike) -> JSONSchema:
        if not is_TypeLike(x):
            raise ValueError(x)
        tr = ipce_from_typelike_tr(x, c=c, ieso=ieso)
        used.update(tr.used)
        return tr.schema

    def fob(x: object) -> IPCE:
        return ipce_from_object(x, globals_=c.globals_, ieso=ieso)

    def f(x: object) -> IPCE:
        if is_TypeLike(x):
            x = cast(TypeLike, x)
            return ftl(x)
        else:
            return fob(x)

    res = cast(JSONSchema, {})

    mentioned = set(get_mentioned_names(T, ()))
    relevant = [x for x in c.context if x in mentioned and x != T.__name__]
    relevant.append(T.__qualname__)
    url_name = "_".join(relevant)
    my_ref = make_url(url_name)
    res[ID_ATT] = my_ref
    res[JSC_TITLE] = T.__name__
    c.processing[T.__name__] = my_ref

    res[ATT_PYTHON_NAME] = T.__qualname__
    res[X_PYTHON_MODULE_ATT] = T.__module__

    res[SCHEMA_ATT] = SCHEMA_ID

    res[JSC_TYPE] = JSC_OBJECT

    if hasattr(T, "__doc__") and T.__doc__ is not None:
        res[JSC_DESCRIPTION] = T.__doc__

    Ti = get_dataclass_info(T)

    definitions = {}
    # bindings: Dict[str, type] = {}

    types2: Tuple[type, ...] = Ti.get_open()
    to_add: Dict[type, type] = {}
    for tx in types2:
        if not isinstance(tx, TypeVar):
            continue
        abound = get_TypeVar_bound(tx)
        to_add[tx] = abound
        c.globals_[tx] = tx

    #
    # for tx, val in Ti.bindings.items():
    #     to_add[tx] = val

    def get_schema_with_url(url, bound):
        schema = ftl(bound)
        schema = copy.copy(schema)
        schema[ID_ATT] = url
        schema = sorted_dict_cbor_ord(schema)
        return schema

    for t2, bound in to_add.items():
        t2_name = get_TypeVar_name(t2)
        url = make_url(f"{T.__qualname__}/{t2_name}")
        schema = get_schema_with_url(url, bound)
        c.processing[t2_name] = url
        if t2 in Ti.get_open():
            definitions[t2_name] = schema
        # if t2 in Ti.bindings:
        #     bindings[t2_name] = schema

    if Ti.orig:
        # res[X_ORIG] = list(get_TypeVar_name(_) for _ in Ti.orig)
        def ff(_) -> JSONSchema:
            if is_TypeVar(_):
                _name = get_TypeVar_name(_)
                url = make_url(f"{T.__qualname__}/{_name}")
                return make_ref(url)
            else:
                return ftl(_)

        res[X_ORIG] = [ff(_) for _ in Ti.orig]
    # if Ti.extra:
    #     res[X_EXTRA] = list(get_TypeVar_name(_) for _ in Ti.extra)

    if definitions:
        res[JSC_DEFINITIONS] = sorted_dict_cbor_ord(definitions)
    # if bindings:
    #     res[X_BINDINGS] = sorted_dict_cbor_ord(bindings)

    properties = {}
    classvars = {}
    classatts = {}

    required = []
    all_fields: Dict[str, Field] = get_fields_including_static(T)

    from .conv_ipce_from_object import ipce_from_object

    original_order = list(all_fields)
    ordered = sorted(all_fields)

    for name in ordered:
        afield = all_fields[name]

        t = afield.type

        try:
            if isinstance(t, str):  # pragma: no cover
                # t = eval_just_string(t, c.globals_)
                msg = "Before serialization, need to have all text references substituted."
                msg += f"\n found reference {t!r} in class {T}."
                raise Exception(msg)

            if is_ClassVar(t):
                tt = get_ClassVar_arg(t)

                classvars[name] = ftl(tt)
                try:
                    the_att = get_T_attribute(T, name)
                except AttributeError:
                    pass
                else:
                    classatts[name] = f(the_att)

            else:  # not classvar
                schema = ftl(t)

                try:
                    default = get_field_default(afield)
                except KeyError:
                    required.append(name)
                else:
                    schema = make_schema_with_default(schema, default, c, ieso)
                properties[name] = schema

        except IPCE_PASS_THROUGH:  # pragma: no cover
            raise
        except BaseException as e:
            msg = "Cannot write schema for attribute @name -> @t of type @T."
            raise ZTypeError(msg, name=name, t=t, T=T) from e

    if required:  # empty is error
        res[JSC_REQUIRED] = sorted(required)
    if classvars:
        res[X_CLASSVARS] = classvars
    if classatts:
        res[X_CLASSATTS] = classatts

    assert len(classvars) >= len(classatts), (classvars, classatts)

    if properties:
        res[JSC_PROPERTIES] = sorted_dict_cbor_ord(properties)

    res[X_ORDER] = original_order
    if sorted_dict_cbor_ord:
        res = sorted_dict_cbor_ord(res)

    if T.__name__ in used:
        used.pop(T.__name__)
    return TRE(res, used)


def get_T_attribute(T: TypeLike, n: str) -> object:
    if hasattr(T, n):
        # special case
        the_att2 = getattr(T, n)
        if isinstance(the_att2, Field):
            # actually attribute not there
            raise AttributeError()
        else:
            return the_att2
    else:
        raise AttributeError()


def make_schema_with_default(
    schema: JSONSchema, default: object, c: IFTContext, ieso: IESO
) -> JSONSchema:
    from .conv_ipce_from_object import ipce_from_object  # ok-ish

    options = [schema]
    s_u_one = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID, ANY_OF: options})

    ipce_default = ipce_from_object(default, globals_=c.globals_, ieso=ieso)
    s_u_one["default"] = ipce_default
    s_u_one = sorted_dict_cbor_ord(s_u_one)
    return s_u_one


from dataclasses import MISSING


def get_field_default(f: Field) -> object:
    if f.default != MISSING:
        return f.default
    elif f.default_factory != MISSING:
        return f.default_factory()
    else:
        raise KeyError("no default")


def ipce_from_typelike_Union(t: TypeLike, c: IFTContext, ieso: IESO) -> TRE:
    types = get_Union_args(t)
    used = {}

    def f(x: TypeLike) -> JSONSchema:
        tr = ipce_from_typelike_tr(x, c=c, ieso=ieso)
        used.update(tr.used)
        return tr.schema

    types = tuple(sorted(types, key=key_for_sorting_types))
    options = [f(t) for t in types]

    res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID, ANY_OF: options})
    res = sorted_dict_cbor_ord(res)
    return TRE(res, used)


def ipce_from_typelike_Optional(t: TypeLike, c: IFTContext, ieso: IESO) -> TRE:
    types = [get_Optional_arg(t), type(None)]
    kt = KeepTrackSer(c, ieso)

    options = [kt.ipce_from_typelike(t) for t in types]
    res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID, ANY_OF: options})
    res = sorted_dict_cbor_ord(res)
    return kt.tre(res)


#
