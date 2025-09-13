import sys
import typing
from abc import ABCMeta, abstractmethod
from dataclasses import _PARAMS, dataclass, fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, cast, ClassVar, Dict, Optional, Tuple, Type, TypeVar

from zuper_commons.types import ZTypeError, ZValueError

from . import logger
from .aliases import TypeLike
from .annotations_tricks import (
    get_ClassVar_arg,
    get_Type_arg,
    get_TypeVar_bound,
    is_ClassVar,
    is_NewType,
    is_Type,
    is_TypeLike,
    make_dict,
    name_for_type_like,
)
from .constants import ANNOTATIONS_ATT, DEPENDS_ATT, MakeTypeCache, PYTHON_36, ZuperTypingGlobals
from .dataclass_info import DataclassInfo, get_dataclass_info, set_dataclass_info
from .recursive_tricks import (
    get_name_without_brackets,
    NoConstructorImplemented,
    replace_typevars,
)
from .subcheck import can_be_used_as2, value_liskov

__all__ = ["resolve_types", "MyABC", "StructuralTyping", "make_type"]

X = TypeVar("X")


def as_tuple(x) -> Tuple:
    return x if isinstance(x, tuple) else (x,)


if PYTHON_36:  # pragma: no cover
    from typing import GenericMeta

    # noinspection PyUnresolvedReferences
    old_one = GenericMeta.__getitem__
else:
    old_one = None

if PYTHON_36:  # pragma: no cover
    # logger.info('In Python 3.6')
    class ZMeta(type):
        def __getitem__(self, *params):
            return ZenericFix.__class_getitem__(*params)


else:
    ZMeta = type


class ZenericFix(metaclass=ZMeta):
    if PYTHON_36:  # pragma: no cover

        def __getitem__(self, *params):
            # logger.info(f'P36 {params} {self}')
            if self is typing.Generic:
                return ZenericFix.__class_getitem__(*params)

            if self is Dict:
                K, V = params
                if K is not str:
                    return make_dict(K, V)

            # noinspection PyArgumentList
            return old_one(self, params)

    # noinspection PyMethodParameters
    @classmethod
    def __class_getitem__(cls0, params):
        # logger.info(f"ZenericFix.__class_getitem__ params = {params}")
        types0 = as_tuple(params)
        assert isinstance(types0, tuple)
        for t in types0:
            assert is_TypeLike(t), (t, types0)

        bound_att = types0
        name = "Generic[%s]" % ",".join(name_for_type_like(_) for _ in bound_att)
        di = DataclassInfo(name=name, orig=bound_att)
        gp = type(name, (GenericProxy,), {"di": di})
        set_dataclass_info(gp, di)
        return gp


#
# def autoInitDecorator(toDecoreFun):
#     def wrapper(*args, **kwargs):
#         print("Hello from autoinit decorator")
#         toDecoreFun(*args, **kwargs)
#
#     return wrapper


class StructuralTyping(type):
    cache = {}

    def __subclasscheck__(self, subclass: type) -> bool:

        key = (self, subclass)
        if key in StructuralTyping.cache:
            return StructuralTyping.cache[key]
        # logger.info(f"{subclass.__name__} <=  {self.__name__}")
        try:
            can = can_be_used_as2(subclass, self)
        except:
            if PYTHON_36:
                return False
            else:
                raise
        res = can.result
        StructuralTyping.cache[key] = res
        return res

    def __instancecheck__(self, instance) -> bool:
        T = type(instance)
        if T is self:
            return True
        if not is_dataclass(T):
            return False
        i = super().__instancecheck__(instance)
        if i:
            return True
        # logger.info(f"in {T.__name__} <=  {self.__name__}")
        # res = can_be_used_as2(T, self)
        return self.__subclasscheck__(T)

        # return res.result


class MyABC(StructuralTyping, ABCMeta):
    def __new__(mcs, name_orig: str, bases, namespace, **kwargs):
        # logger.info(name_orig=name_orig, bases=bases, namespace=namespace, kwargs=kwargs)

        clsi = None

        if "di" in namespace:
            clsi = cast(DataclassInfo, namespace["di"])
            # logger.info('got clsi from namespace', clsi)
        else:
            if bases:
                # this is when we subclass

                base_info = get_dataclass_info(bases[-1])
                clsi = DataclassInfo(name="", orig=base_info.get_open())

                # logger.info('got clsi from subclass', base_info=base_info, clsi=clsi)

        if clsi is None:
            default = DataclassInfo(name=name_orig, orig=())
            clsi = default

        name = clsi.name = get_name_for(name_orig, clsi)

        # noinspection PyArgumentList
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        qn = cls.__qualname__.replace("." + name_orig, "." + name)

        setattr(cls, "__qualname__", qn)
        # logger.info(f" old module {cls.__module__} new {mcs.__module__}")

        # setattr(cls, "__module__", mcs.__module__)

        set_dataclass_info(cls, clsi)

        return cls


def get_name_for(name_orig: str, clsi: DataclassInfo) -> str:
    name0 = get_name_without_brackets(name_orig)
    params = []
    for x in clsi.orig:
        # params.append(replace_typevars(x, bindings=clsi.bindings, symbols={}))
        params.append(x)
    if not params:
        return name0
    else:
        name = f"{name0}[%s]" % (",".join(name_for_type_like(_) for _ in params))
        return name


if PYTHON_36:  # pragma: no cover

    class FakeGenericMeta(MyABC):
        def __getitem__(self, params2):
            clsi = get_dataclass_info(self)
            types_open = clsi.get_open()

            types2 = as_tuple(params2)

            assert isinstance(types2, tuple), types2
            for t in types2:
                assert is_TypeLike(t), (t, types2)

            if types_open == types2:
                return self

            bindings: Dict[TypeVar, TypeVar] = {}
            for T, U in zip(types_open, types2):
                bindings[T] = U
                bound = get_TypeVar_bound(T)

                if bound is not None:
                    try:
                        can = can_be_used_as2(U, bound)
                    except (TypeError, ValueError) as e:
                        if PYTHON_36:
                            continue
                        else:
                            raise
                        # raise ZTypeError(U=U, bound=bound) from e
                    else:
                        if not can:
                            msg = (
                                f'For type parameter "{name_for_type_like(T)}", expected a '
                                f'subclass of "{name_for_type_like(bound)}", found {U}.'
                            )
                            raise ZTypeError(msg, can=can, T=T, bound=bound, U=U)
            return make_type(self, bindings)


else:
    FakeGenericMeta = MyABC


class GenericProxy(metaclass=FakeGenericMeta):
    @abstractmethod
    def need(self) -> None:
        """"""

    @classmethod
    def __class_getitem__(cls, params2) -> type:
        clsi = get_dataclass_info(cls)
        types_open = clsi.get_open()
        types2 = as_tuple(params2)

        if len(types_open) != len(types2):
            msg = "Cannot match type length"
            raise ZValueError(
                msg, cls=cls.__name__, clsi=get_dataclass_info(cls), types=types_open, types2=types2
            )

        bindings = {}

        for T, U in zip(types_open, types2):
            bindings[T] = U
            bound = get_TypeVar_bound(T)
            if (bound is not None) and (bound is not object) and isinstance(bound, type):
                # logger.info(f"{U} should be usable as {T.__bound__}")
                # logger.info(
                #     f" issubclass({U}, {T.__bound__}) ="
                #     f" {issubclass(U, T.__bound__)}"
                # )
                try:
                    # issub = issubclass(U, bound)
                    issub = can_be_used_as2(U, bound)
                except TypeError as e:
                    msg = ""
                    raise ZTypeError(msg, T=T, T_bound=bound, U=U) from e

                if not issub:
                    msg = (
                        f'For type parameter "{T.__name__}", expected a'
                        f'subclass of "{bound.__name__}", found @U.'
                    )
                    raise ZTypeError(msg, T=T, T_bound=bound, U=U)

        res = make_type(cls, bindings)
        # from .monkey_patching_typing import remember_created_class
        #
        # remember_created_class(res, "__class_getitem__")
        return res


class Fake:
    symbols: dict
    myt: type

    def __init__(self, myt, symbols: dict):
        self.myt = myt
        n = name_for_type_like(myt)
        self.name_without = get_name_without_brackets(n)
        self.symbols = symbols

    def __getitem__(self, item: type) -> type:

        n = name_for_type_like(item)
        complete = f"{self.name_without}[{n}]"
        if complete in self.symbols:
            res = self.symbols[complete]
        else:
            # noinspection PyUnresolvedReferences
            res = self.myt[item]

        # myt = self.myt, symbols = self.symbols,
        # d = debug_print(dict(item=item, res=res))
        # logger.error(f"Fake:getitem", myt=self.myt, item=item, res=res)
        return res


def resolve_types(T, locals_=None, refs: Tuple = (), nrefs: Optional[Dict[str, Any]] = None):
    if nrefs is None:
        nrefs = {}

    assert is_dataclass(T)
    clsi = get_dataclass_info(T)
    # rl = RecLogger()

    if locals_ is None:
        locals_ = {}
    symbols = dict(locals_)

    for k, v in nrefs.items():
        symbols[k] = v

    others = getattr(T, DEPENDS_ATT, ())

    for t in (T,) + refs + others:
        n = name_for_type_like(t)
        symbols[n] = t
        # logger.info(f't = {t} n {n}')
        name_without = get_name_without_brackets(n)

        # if name_without in ['Union', 'Dict', ]:
        #     # FIXME please add more here
        #     continue
        if name_without not in symbols:
            symbols[name_without] = Fake(t, symbols)
        # else:
        #     pass

    for x in clsi.get_open():  # (T, GENERIC_ATT2, ()):
        if hasattr(x, "__name__"):
            symbols[x.__name__] = x

    # logger.debug(f'symbols: {symbols}')
    annotations: Dict[str, TypeLike] = getattr(T, ANNOTATIONS_ATT, {})
    # add in case it was not there
    setattr(T, ANNOTATIONS_ATT, annotations)

    for k, v in annotations.items():
        if not isinstance(v, str) and is_ClassVar(v):
            continue  # XXX
        v = cast(TypeLike, v)
        try:
            r = replace_typevars(v, bindings={}, symbols=symbols)
            # rl.p(f'{k!r} -> {v!r} -> {r!r}')
            annotations[k] = r
        except NameError:
            # msg = (
            #     f"resolve_type({T.__name__}):"
            #     f' Cannot resolve names for attribute "{k}" = {v!r}.'
            # )
            # msg += f'\n symbols: {symbols}'
            # msg += '\n\n' + indent(traceback.format_exc(), '', '> ')
            # raise NameError(msg) from e
            # logger.warning(msg)
            continue
        except TypeError as e:  # pragma: no cover
            msg = f'Cannot resolve type for attribute "{k}".'
            raise ZTypeError(msg) from e
    for f in fields(T):
        assert f.name in annotations
        # msg = f'Cannot get annotation for field {f.name!r}'
        # logger.warning(msg)
        # continue
        # logger.info(K=T.__name__, name=f.name, before=f.type, after=annotations[f.name],
        #             a=annotations[f.name].__dict__)
        f.type = annotations[f.name]
    # logger.info(K=T.__name__, anns=getattr(T, '__annotations__',"?"), annotations=annotations)


def type_check(type_self: type, k: str, T_expected: type, value_found: object):
    try:
        enable_difficult = ZuperTypingGlobals.enable_type_checking_difficult
        T_found = type(value_found)
        simple = T_found in [int, float, bool, str, bytes, Decimal, datetime]
        definitely_exclude = T_found in [dict, list, tuple]
        do_it = (not definitely_exclude) and (enable_difficult or simple)
        if do_it:

            ok = value_liskov(value_found, T_expected)
            if not ok:  # pragma: no cover
                type_self_name = name_for_type_like(type_self)
                # T_expected_name = name_for_type_like(T_expected)
                # T_found_name = name_for_type_like(T_found)
                msg = f"Error for field {k!r} of class {type_self_name}"

                # warnings.warn(msg, stacklevel=3)
                raise ZValueError(
                    msg,
                    field=k,
                    why=ok,
                    expected_type=T_expected,
                    found_value=value_found,
                    found_type=type(value_found),
                )
    except TypeError as e:  # pragma: no cover
        msg = f"Cannot judge annotation of {k} (supposedly {value_found!r})."

        if sys.version_info[:2] == (3, 6):
            # FIXME: warn
            return
        logger.error(msg)
        raise TypeError(msg) from e


def make_type(
    cls: Type[dataclass],
    bindings: Dict[type, type],  # TypeVars
    symbols: Optional[Dict[str, type]] = None,
) -> type:
    if symbols is None:
        symbols = {}

    clsi = get_dataclass_info(cls)
    key = tuple(bindings.items()) + tuple(symbols.items())
    if key in clsi.specializations:
        return clsi.specializations[key]

    try:
        res = make_type_(cls, bindings, symbols)

    except ZValueError as e:  # pragma: no cover
        msg = "Cannot run make_type"
        raise ZValueError(msg, cls=cls, bindings=bindings, symbols=symbols) from e

    clsi.specializations[key] = res
    return res


def make_type_(
    cls: Type[dataclass],
    bindings0: Dict[type, type],  # TypeVars
    symbols: Optional[Dict[str, type]] = None,
) -> type:
    clsi = get_dataclass_info(cls)

    # We only allow the binding of the open ones
    bindings: Dict[type, type] = {}
    open = clsi.get_open()
    for k, v in bindings0.items():
        if k in open:
            bindings[k] = v
        else:
            pass

    if not bindings:
        return cls

    if symbols is None:
        symbols = {}
    symbols = dict(symbols)
    refs = getattr(cls, DEPENDS_ATT, ())
    for r in refs:
        # n = name_for_type_like(r)
        n = r.__name__
        symbols[get_name_without_brackets(n)] = r

    assert not is_NewType(cls), cls

    cache_key = (str(cls), str(bindings), str(clsi.orig))
    if ZuperTypingGlobals.cache_enabled:
        if cache_key in MakeTypeCache.cache:
            # logger.info(f"using cached value for {cache_key}")
            return MakeTypeCache.cache[cache_key]

    recur = lambda _: replace_typevars(_, bindings=bindings, symbols=symbols)

    new_bindings = bindings

    # its_globals = dict(sys.modules[cls.__module__].__dict__)
    # # its_globals[get_name_without_brackets(cls.__name__)] = cls
    # try:
    #     annotations = typing.get_type_hints(cls, its_globals)
    # except:
    #     logger.info(f'globals for {cls.__name__}', cls.__module__, list(its_globals))
    #     raise

    annotations = getattr(cls, ANNOTATIONS_ATT, {})
    name_without = get_name_without_brackets(cls.__name__)

    def param_name(x: type) -> str:
        x = replace_typevars(x, bindings=new_bindings, symbols=symbols)
        return name_for_type_like(x)

    if clsi.orig:
        pnames = tuple(param_name(_) for _ in clsi.orig)
        name2 = "%s[%s]" % (name_without, ",".join(pnames))
    else:
        name2 = name_without
    try:
        # def __new__(_cls, *args, **kwargs):
        #     print('creating object')
        #     x = super().__new__(_cls, *args, **kwargs)
        #     return x

        cls2 = type(name2, (cls,), {"need": lambda: None})
        # cls2.__new__ = __new__
    except TypeError as e:  # pragma: no cover
        msg = f'Cannot create derived class "{name2}" from the class.'
        raise ZTypeError(msg, cls=cls) from e

    symbols[name2] = cls2
    symbols[cls.__name__] = cls2  # also MyClass[X] should resolve to the same
    MakeTypeCache.cache[cache_key] = cls2

    class Fake2:
        def __getitem__(self, item):
            n = name_for_type_like(item)
            complete = f"{name_without}[{n}]"
            if complete in symbols:
                return symbols[complete]

            logger.info(f"Fake2:getitem", name_for_type_like(cls), complete=complete)
            # noinspection PyUnresolvedReferences
            return cls[item]

    if name_without not in symbols:
        symbols[name_without] = Fake2()

    for T, U in bindings.items():
        symbols[T.__name__] = U
        if hasattr(U, "__name__"):
            # dict does not have name
            symbols[U.__name__] = U

    new_annotations = {}

    for k, v0 in annotations.items():
        v = recur(v0)

        # print(f'{v0!r} -> {v!r}')
        if is_ClassVar(v):
            s = get_ClassVar_arg(v)
            if is_Type(s):
                st = get_Type_arg(s)
                concrete = recur(st)

                new_annotations[k] = ClassVar[type]
                setattr(cls2, k, concrete)
            else:
                s2 = recur(s)
                new_annotations[k] = ClassVar[s2]
        else:
            new_annotations[k] = v

    original__post_init__ = getattr(cls, "__post_init__", None)

    if ZuperTypingGlobals.enable_type_checking:

        def __post_init__(self):
            # do it first (because they might change things around)
            if original__post_init__ is not None:
                original__post_init__(self)

            for k, T_expected in new_annotations.items():
                if is_ClassVar(T_expected):
                    continue
                if isinstance(T_expected, type):
                    val = getattr(self, k)
                    type_check(type(self), k=k, value_found=val, T_expected=T_expected)

        # important: do it before dataclass
        setattr(cls2, "__post_init__", __post_init__)

    cls2.__annotations__ = new_annotations

    # logger.info('new annotations: %s' % new_annotations)
    if is_dataclass(cls):

        frozen = is_frozen(cls)

        cls2 = dataclass(cls2, unsafe_hash=True, frozen=frozen)

    else:
        # noinspection PyUnusedLocal
        def init_placeholder(self, *args, **kwargs):
            if args or kwargs:
                msg = (
                    f"Default constructor of {cls2.__name__} does not know  "
                    f"what to do with arguments."
                )
                msg += f"\nargs: {args!r}\nkwargs: {kwargs!r}"
                msg += f"\nself: {self}"
                msg += f"\nself: {dir(type(self))}"
                msg += f"\nself: {type(self)}"
                raise NoConstructorImplemented(msg)

        if cls.__init__ == object.__init__:
            setattr(cls2, "__init__", init_placeholder)

    cls2.__module__ = cls.__module__
    setattr(cls2, "__name__", name2)

    setattr(cls2, "__doc__", getattr(cls, "__doc__"))

    qn = cls.__qualname__
    qn0, sep, _ = qn.rpartition(".")
    if not sep:
        sep = ""
    setattr(cls2, "__qualname__", qn0 + sep + name2)

    orig2 = tuple(replace_typevars(x, bindings=new_bindings, symbols=symbols) for x in clsi.orig)
    clsi2 = DataclassInfo(name=name2, orig=orig2)
    set_dataclass_info(cls2, clsi2)

    MakeTypeCache.cache[cache_key] = cls2

    return cls2


def is_frozen(t):
    return getattr(t, _PARAMS).frozen
