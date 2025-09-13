import dataclasses
import datetime
from dataclasses import dataclass, field, Field, make_dataclass, MISSING
from decimal import Decimal
from numbers import Number
from typing import (
    Any,
    Callable,
    cast,
    ClassVar,
    Dict,
    List,
    NewType,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

import numpy as np

from zuper_commons.types import (
    check_isinstance,
    ZException,
    ZNotImplementedError,
    ZTypeError,
    ZValueError,
)
from zuper_typing import (
    DataclassInfo,
    get_remembered_class,
    is_ClassVar,
    is_ForwardRef,
    is_placeholder,
    make_dict,
    make_Intersection,
    make_list,
    make_Literal,
    make_set,
    make_Tuple,
    make_Union,
    make_VarTuple,
    MyABC,
    MyNamedArg,
    PYTHON_36,
    recursive_type_subst,
    remember_created_class,
    set_dataclass_info,
)
from . import logger
from .constants import (
    ATT_PYTHON_NAME,
    CALLABLE_ORDERING,
    CALLABLE_RETURN,
    ID_ATT,
    IEDO,
    IEDS,
    JSC_ADDITIONAL_PROPERTIES,
    JSC_ALLOF,
    JSC_ANYOF,
    JSC_ARRAY,
    JSC_BOOL,
    JSC_DEFAULT,
    JSC_DEFINITIONS,
    JSC_DESCRIPTION,
    JSC_ENUM,
    JSC_INTEGER,
    JSC_NULL,
    JSC_NUMBER,
    JSC_OBJECT,
    JSC_PROPERTIES,
    JSC_REQUIRED,
    JSC_STRING,
    JSC_TITLE,
    JSC_TITLE_BYTES,
    JSC_TITLE_CALLABLE,
    JSC_TITLE_DATETIME,
    JSC_TITLE_DECIMAL,
    JSC_TITLE_FLOAT,
    JSC_TITLE_NUMPY,
    JSC_TITLE_SLICE,
    JSC_TYPE,
    JSONSchema,
    REF_ATT,
    SCHEMA_ATT,
    SCHEMA_ID,
    X_CLASSATTS,
    X_CLASSVARS,
    X_ORDER,
    X_ORIG,
    X_PYTHON_MODULE_ATT,
)
from .structures import CannotFindSchemaReference
from .types import IPCE, is_unconstrained, TypeLike

_X = TypeVar("_X")


@dataclass
class SRE:
    res: TypeLike
    used: Dict[str, object] = dataclasses.field(default_factory=dict)


# XXX: same class?
@dataclass
class SRO:
    res: object
    used: Dict[str, object] = dataclasses.field(default_factory=dict)


def typelike_from_ipce(schema0: JSONSchema, *, iedo: Optional[IEDO] = None) -> TypeLike:
    if iedo is None:
        iedo = IEDO(use_remembered_classes=False, remember_deserialized_classes=False)
    ieds = IEDS({}, {})
    sre = typelike_from_ipce_sr(schema0, ieds=ieds, iedo=iedo)
    #
    # try:
    #     assert_equivalent_types(sre.res, sre.res)
    # except Exception as e:
    #     raise ZValueError(sre=sre) from e

    return sre.res


def typelike_from_ipce_sr(schema0: JSONSchema, *, ieds: IEDS, iedo: IEDO) -> SRE:
    try:
        sre = typelike_from_ipce_sr_(schema0, ieds=ieds, iedo=iedo)
        assert isinstance(sre, SRE), (schema0, sre)
        res = sre.res
    except (TypeError, ValueError) as e:  # pragma: no cover
        msg = "Cannot interpret schema as a type."
        raise ZTypeError(msg, schema0=schema0) from e

    if ID_ATT in schema0:
        schema_id = schema0[ID_ATT]
        ieds.encountered[schema_id] = res

    return sre


def typelike_from_ipce_sr_(schema0: JSONSchema, *, ieds: IEDS, iedo: IEDO) -> SRE:
    # pprint('schema_to_type_', schema0=schema0)
    # encountered = encountered or {}

    check_isinstance(schema0, dict)
    schema = cast(JSONSchema, dict(schema0))
    # noinspection PyUnusedLocal
    metaschema = schema.pop(SCHEMA_ATT, None)
    schema_id = schema.pop(ID_ATT, None)
    if schema_id:
        if not JSC_TITLE in schema:
            pass
        else:
            cls_name = schema[JSC_TITLE]
            ieds.encountered[schema_id] = cls_name

    if JSC_ENUM in schema0:
        schema1 = dict(schema0)
        enum = schema1.pop(JSC_ENUM)
        schema1 = cast(JSONSchema, schema1)
        return typelike_from_ipce_enum(schema1, enum, ieds=ieds, iedo=iedo)

    if schema == {JSC_TITLE: "Any"}:
        return SRE(Any)
    if schema == {}:
        return SRE(object)
    if schema == {JSC_TITLE: "object"}:
        return SRE(object)

    if REF_ATT in schema:
        r = schema[REF_ATT]
        if r == SCHEMA_ID:
            if schema.get(JSC_TITLE, "") == "type":
                return SRE(type)
            else:  # pragma: no cover
                raise ZNotImplementedError(schema=schema)
                # return SRE(Type)

        if r in ieds.encountered:
            res = ieds.encountered[r]
            if is_placeholder(res):
                used = {r: res}
            else:
                used = {}
            return SRE(res, used=used)
        else:
            msg = f"Cannot evaluate reference {r!r}"

            raise CannotFindSchemaReference(msg, ieds=ieds)

    if JSC_ANYOF in schema:
        return typelike_from_ipce_Union(schema, ieds=ieds, iedo=iedo)

    if JSC_ALLOF in schema:
        return typelike_from_ipce_Intersection(schema, ieds=ieds, iedo=iedo)

    jsc_type = schema.get(JSC_TYPE, None)
    jsc_title = schema.get(JSC_TITLE, "-not-provided-")
    if jsc_title == JSC_TITLE_NUMPY:
        res = np.ndarray
        return SRE(res)

    if jsc_type == "NewType":
        kt = KeepTrackDes(ieds, iedo)
        if "newtype" not in schema:
            original = object
        else:
            nt = schema["newtype"]
            tre = typelike_from_ipce_sr(nt, ieds=ieds, iedo=iedo)
            original = tre.res

        res = NewType(jsc_title, original)
        return kt.sre(res)

    if jsc_type == JSC_STRING:
        if jsc_title == JSC_TITLE_BYTES:
            return SRE(bytes)
        elif jsc_title == JSC_TITLE_DATETIME:
            return SRE(datetime.datetime)
        elif jsc_title == JSC_TITLE_DECIMAL:
            return SRE(Decimal)
        else:
            return SRE(str)
    elif jsc_type == JSC_NULL:
        return SRE(type(None))

    elif jsc_type == JSC_BOOL:
        return SRE(bool)

    elif jsc_type == JSC_NUMBER:
        if jsc_title == JSC_TITLE_FLOAT:
            return SRE(float)
        else:
            return SRE(Number)

    elif jsc_type == JSC_INTEGER:
        return SRE(int)
    elif jsc_type == "subtype":
        s = schema["subtype"]
        r = typelike_from_ipce_sr(s, ieds=ieds, iedo=iedo)
        T = Type[r.res]
        return SRE(T, r.used)

    elif jsc_type == JSC_OBJECT:
        if jsc_title == JSC_TITLE_CALLABLE:
            return typelike_from_ipce_Callable(schema, ieds=ieds, iedo=iedo)
        elif jsc_title.startswith("Dict["):
            return typelike_from_ipce_DictType(schema, ieds=ieds, iedo=iedo)
        elif jsc_title.startswith("Set["):
            return typelike_from_ipce_SetType(schema, ieds=ieds, iedo=iedo)
        elif jsc_title == JSC_TITLE_SLICE:
            return SRE(slice)
        else:
            return typelike_from_ipce_dataclass(schema, schema_id=schema_id, ieds=ieds, iedo=iedo)

    elif jsc_type == JSC_ARRAY:
        return typelike_from_ipce_array(schema, ieds=ieds, iedo=iedo)

    msg = "Cannot recover schema"
    raise ZValueError(msg, schema=schema)
    # assert False, schema  # pragma: no cover


def typelike_from_ipce_enum(schema: JSONSchema, enum: List[object], *, ieds: IEDS, iedo: IEDO):
    kt = KeepTrackDes(ieds, iedo)
    T = kt.typelike_from_ipce(schema)
    values = [kt.object_from_ipce(_, T) for _ in enum]
    res = make_Literal(*tuple(values))
    return kt.sre(res)


def typelike_from_ipce_Union(schema, *, ieds: IEDS, iedo: IEDO) -> SRE:
    options = schema[JSC_ANYOF]
    kt = KeepTrackDes(ieds, iedo)

    args = [kt.typelike_from_ipce(_) for _ in options]
    if args and args[-1] is type(None):
        V = args[0]
        res = Optional[V]
    else:
        res = make_Union(*args)
    return kt.sre(res)


def typelike_from_ipce_Intersection(schema, *, ieds: IEDS, iedo: IEDO) -> SRE:
    options = schema[JSC_ALLOF]
    kt = KeepTrackDes(ieds, iedo)

    args = [kt.typelike_from_ipce(_) for _ in options]
    res = make_Intersection(tuple(args))
    return kt.sre(res)


class KeepTrackDes:
    def __init__(self, ieds: IEDS, iedo: IEDO):
        self.ieds = ieds
        self.iedo = iedo
        self.used = {}

    def typelike_from_ipce(self, x: IPCE):
        sre = typelike_from_ipce_sr(x, ieds=self.ieds, iedo=self.iedo)
        self.used.update(sre.used)
        return sre.res

    def object_from_ipce(self, x: IPCE, st: Type[_X] = object) -> _X:
        from .conv_object_from_ipce import object_from_ipce_

        res = object_from_ipce_(x, st, ieds=self.ieds, iedo=self.iedo)
        return res

    def sre(self, x: IPCE) -> SRE:
        return SRE(x, self.used)


def typelike_from_ipce_array(schema, *, ieds: IEDS, iedo: IEDO) -> SRE:
    assert schema[JSC_TYPE] == JSC_ARRAY
    items = schema["items"]
    kt = KeepTrackDes(ieds, iedo)

    if isinstance(items, list):
        # assert len(items) > 0
        args = tuple([kt.typelike_from_ipce(_) for _ in items])
        res = make_Tuple(*args)

    else:
        if schema[JSC_TITLE].startswith("Tuple["):
            V = kt.typelike_from_ipce(items)
            res = make_VarTuple(V)

        else:
            V = kt.typelike_from_ipce(items)
            res = make_list(V)

    # logger.info(f'found list like: {res}')
    return kt.sre(res)


def typelike_from_ipce_DictType(schema, *, ieds: IEDS, iedo: IEDO) -> SRE:
    K = str
    kt = KeepTrackDes(ieds, iedo)

    V = kt.typelike_from_ipce(schema[JSC_ADDITIONAL_PROPERTIES])
    # pprint(f'here:', d=dict(V.__dict__))
    # if issubclass(V, FakeValues):
    if isinstance(V, type) and V.__name__.startswith("FakeValues"):
        K = V.__annotations__["real_key"]
        V = V.__annotations__["value"]

    try:
        D = make_dict(K, V)
    except (TypeError, ValueError) as e:  # pragma: no cover
        msg = f"Cannot reconstruct dict type."

        raise ZTypeError(msg, K=K, V=V, ieds=ieds) from e

    return kt.sre(D)


def typelike_from_ipce_SetType(schema, *, ieds: IEDS, iedo: IEDO):
    if not JSC_ADDITIONAL_PROPERTIES in schema:  # pragma: no cover
        msg = f"Expected {JSC_ADDITIONAL_PROPERTIES!r} in @schema."
        raise ZValueError(msg, schema=schema)

    kt = KeepTrackDes(ieds, iedo)

    V = kt.typelike_from_ipce(schema[JSC_ADDITIONAL_PROPERTIES])
    res = make_set(V)
    return kt.sre(res)


def typelike_from_ipce_Callable(schema: JSONSchema, *, ieds: IEDS, iedo: IEDO):
    kt = KeepTrackDes(ieds, iedo)

    schema = dict(schema)
    definitions = dict(schema[JSC_DEFINITIONS])
    ret = kt.typelike_from_ipce(definitions.pop(CALLABLE_RETURN))
    others = []
    for k in schema[CALLABLE_ORDERING]:
        d = kt.typelike_from_ipce(definitions[k])
        if not looks_like_int(k):
            d = MyNamedArg(d, k)
        others.append(d)

    # noinspection PyTypeHints
    res = Callable[others, ret]
    # logger.info(f'typelike_from_ipce_Callable: {schema} \n others =  {others}\n res = {res}')
    return kt.sre(res)


def looks_like_int(k: str) -> bool:
    try:
        int(k)
    except:
        return False
    else:
        return True


def typelike_from_ipce_dataclass(
    res: JSONSchema, schema_id: Optional[str], *, ieds: IEDS, iedo: IEDO
) -> SRE:
    kt = KeepTrackDes(ieds, iedo)

    assert res[JSC_TYPE] == JSC_OBJECT
    cls_name = res[JSC_TITLE]

    definitions = res.get(JSC_DEFINITIONS, {})
    # bindings_ipce = res.get(X_BINDINGS, {})

    required = res.get(JSC_REQUIRED, [])

    properties = res.get(JSC_PROPERTIES, {})
    classvars = res.get(X_CLASSVARS, {})
    classatts = res.get(X_CLASSATTS, {})

    if (not X_PYTHON_MODULE_ATT in res) or (not ATT_PYTHON_NAME in res):  # pragma: no cover
        msg = f"Cannot find attributes for {cls_name!r}."
        raise ZValueError(msg, res=res)
    module_name = res[X_PYTHON_MODULE_ATT]
    qual_name = res[ATT_PYTHON_NAME]
    key = (module_name, qual_name)

    if iedo.use_remembered_classes:
        try:
            res = get_remembered_class(module_name, qual_name)
            return SRE(res)
        except KeyError:
            pass
    if key in ieds.klasses:
        return SRE(ieds.klasses[key], {})

    typevars: List[TypeVar] = []
    typevars_dict: Dict[str, type] = {}
    for tname, t in definitions.items():
        bound = kt.typelike_from_ipce(t)
        # noinspection PyTypeHints
        if is_unconstrained(bound):
            bound = None
        # noinspection PyTypeHints
        tv = TypeVar(tname, bound=bound)
        typevars_dict[tname] = tv
        typevars.append(tv)
        if ID_ATT in t:
            ieds.encountered[t[ID_ATT]] = tv

    if typevars:
        typevars2: Tuple[TypeVar, ...] = tuple(typevars)
        from zuper_typing import Generic

        # TODO: typevars
        if PYTHON_36:  # pragma: no cover
            # noinspection PyUnresolvedReferences
            # base = Generic.__getitem__(typevars2)
            base = Generic.__class_getitem__(typevars2)
        else:
            # noinspection PyUnresolvedReferences
            base = Generic.__class_getitem__(typevars2)

        # ztinfo("", base=base, type_base=type(base))
        bases = (base,)
    else:

        class B(metaclass=MyABC):
            pass

        bases = (B,)

    Placeholder = type(f"PlaceholderFor{cls_name}", (), {})

    ieds.encountered[schema_id] = Placeholder

    fields_triples: List[Tuple[str, TypeLike, Field]] = []  # (name, type, Field)

    if X_ORDER in res:
        ordered = res[X_ORDER]
    else:
        ordered = list(properties) + list(classvars) + list(classatts)
    # assert_equal(set(names), set(properties), msg=yaml.dump(res))
    # else:
    #     names = list(properties)
    #

    # logger.info(f'reading {cls_name} names {names}')
    # other_set_attr = {}
    for pname in ordered:
        if pname in properties:
            v = properties[pname]
            ptype = kt.typelike_from_ipce(v)
            _Field = field()
            _Field.name = pname
            has_default = JSC_DEFAULT in v
            if has_default:
                default_value = kt.object_from_ipce(v[JSC_DEFAULT], ptype)
                if isinstance(default_value, (list, dict, set)):
                    _Field.default_factory = MyDefaultFactory(default_value)
                else:
                    _Field.default = default_value

                assert not isinstance(default_value, dataclasses.Field)
                # other_set_attr[pname] = default_value
            else:
                if not pname in required:
                    msg = f"Field {pname!r} is not required but I did not find a default"
                    raise ZException(msg, res=res)
            fields_triples.append((pname, ptype, _Field))
        elif pname in classvars:
            v = classvars[pname]
            ptype = kt.typelike_from_ipce(v)
            # logger.info(f'ipce classvar: {pname} {ptype}')
            f = field()
            if pname in classatts:
                f.default = kt.object_from_ipce(classatts[pname], object)
            fields_triples.append((pname, ClassVar[ptype], f))
        elif pname in classatts:  # pragma: no cover
            msg = f"Found {pname!r} in @classatts but not in @classvars"
            raise ZValueError(msg, res=res, classatts=classatts, classvars=classvars)
        else:  # pragma: no cover
            msg = f"Cannot find {pname!r} either in @properties or @classvars or @classatts."
            raise ZValueError(msg, properties=properties, classvars=classvars, classatts=classatts)
    check_fields_order(fields_triples)
    # ztinfo('fields', fields_triples=fields_triples)
    unsafe_hash = True
    try:
        T = make_dataclass(
            cls_name,
            fields_triples,
            bases=bases,
            namespace=None,
            init=True,
            repr=True,
            eq=True,
            order=True,
            unsafe_hash=unsafe_hash,
            frozen=False,
        )
    except TypeError:  # pragma: no cover
        #
        # msg = "Cannot make dataclass with fields:"
        # for f in fields:
        #     msg += f"\n {f}"
        # logger.error(msg)
        raise
    setattr(T, "__name__", cls_name)

    # logger.info("before fix_anno\n" + debug_print(dict(T=T, ieds=ieds)))
    fix_annotations_with_self_reference(T, cls_name, Placeholder)

    for pname, v in classatts.items():
        if isinstance(v, dict) and SCHEMA_ATT in v and v[SCHEMA_ATT] == SCHEMA_ID:
            interpreted = kt.typelike_from_ipce(cast(JSONSchema, v))
        else:
            interpreted = kt.object_from_ipce(v, object)
        assert not isinstance(interpreted, dataclasses.Field)
        # logger.info("setting class att", pname, interpreted)
        setattr(T, pname, interpreted)

    if JSC_DESCRIPTION in res:
        setattr(T, "__doc__", res[JSC_DESCRIPTION])
    else:
        # we don't want the stock dataclass
        setattr(T, "__doc__", None)
    #     logger.info(f"Did find __doc__ for {T.__name__} {id(T)}")
    # else:
    #     logger.error(f"Did not find __doc__ for {T.__name__} {id(T)}", res=res)
    #     # the original one did not have it
    #     # setattr(T, "__doc__", None)
    #     raise ValueError()

    setattr(T, "__module__", module_name)
    setattr(T, "__qualname__", qual_name)
    used = kt.used
    if schema_id in used:
        used.pop(schema_id)
    if not used:
        if iedo.remember_deserialized_classes:
            remember_created_class(T, "typelike_from_ipce")
        ieds.klasses[key] = T
    else:
        msg = f"Cannot remember {key} because used = {used}"
        logger.warning(msg)
    # logger.info(f"Estimated class {key} used = {used} ")
    # assert not "varargs" in T.__dict__, T
    # ztinfo("typelike_from_ipce", T=T, type_T=type(T), bases=bases)

    # bindings = {}
    # for tname, t in bindings_ipce.items():
    #     u = make_TypeVar(tname)
    #     bindings[u] = kt.typelike_from_ipce(t)

    orig = res.get(X_ORIG, [])

    # extra = res.get(X_EXTRA, [])
    #
    # def make_tv(tname: str) -> type:
    #     if tname in typevars_dict:
    #         return typevars_dict[tname]
    #     else:
    #         return make_TypeVar(tname)

    clsi_orig = []
    for o in orig:
        oT = kt.typelike_from_ipce(o)
        clsi_orig.append(oT)
    # clsi_orig = tuple(make_tv(_) for _ in orig)
    clsi_orig = tuple(clsi_orig)
    # clsi_extra = tuple(make_tv(_) for _ in extra)
    clsi = DataclassInfo(
        name=cls_name,
        # bindings=bindings,
        orig=clsi_orig,
    )
    # extra=clsi_extra)
    set_dataclass_info(T, clsi)

    # try:
    #     assert_equivalent_types(T,T)
    # except Exception as e:
    #     msg = 'I did not create a well-formed class'
    #     raise ZAssertionError(msg, T=T, used=used, ieds=ieds) from e

    return SRE(T, used)


def field_has_default(f: Field) -> bool:
    if f.default != MISSING:
        return True
    elif f.default_factory != MISSING:
        return True
    else:
        return False


def check_fields_order(fields_triples: List[Tuple[str, TypeLike, Field]]):
    found_default = None
    for name, type_, f in fields_triples:
        if is_ClassVar(type_):
            continue
        if field_has_default(f):
            found_default = name
        else:
            if found_default:
                msg = (
                    f"Found out of order fields. Field {name!r} without default found after "
                    f"{found_default!r}."
                )
                raise ZValueError(msg, fields_triples=fields_triples)


def fix_annotations_with_self_reference(
    T: Type[dataclass], cls_name: str, Placeholder: type
) -> None:
    # print('fix_annotations_with_self_reference')
    # logger.info(f'fix_annotations_with_self_reference {cls_name}, placeholder: {Placeholder}')
    # logger.info(f'encountered: {encountered}')
    # logger.info(f'global_symbols: {global_symbols}')

    def f(M: TypeLike) -> TypeLike:
        assert not is_ForwardRef(M)
        if M is Placeholder:
            return T
        if hasattr(M, "__name__") and "Placeholder" in M.__name__:
            pass
            # logger.debug('Found this placeholder',  M=M, T=T, Placeholder=Placeholder)

        if hasattr(M, "__name__") and M.__name__ == Placeholder.__name__:
            # logger.debug('Placeholder of different class')
            return T
        # elif hasattr(M, '__name__') and M.__name__ == Placeholder.__name__:
        #     return T
        else:
            return M

    f.__name__ = f"replacer_for_{cls_name}"

    anns2 = {}

    anns: dict = T.__annotations__

    items = list(anns.items())
    for k, v0 in items:
        anns2[k] = recursive_type_subst(v0, f)
        del k, v0

    T.__annotations__ = anns2

    for fi in dataclasses.fields(T):
        fi.type = T.__annotations__[fi.name]

    # if T.__name__ == 'FailedResult':
    #
    #     logger.info('substituted', anns=anns, anns2=anns2)


class MyDefaultFactory:
    def __init__(self, value: object):
        self.value = value

    def __call__(self) -> object:
        v = self.value
        return type(v)(v)
