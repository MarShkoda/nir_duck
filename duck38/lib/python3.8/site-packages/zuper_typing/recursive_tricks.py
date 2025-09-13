from datetime import datetime
from decimal import Decimal
from numbers import Number
from typing import (
    Any,
    Awaitable,
    cast,
    ClassVar,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from zuper_commons.types import ZNotImplementedError, ZTypeError, ZValueError
from . import logger
from .aliases import TypeLike
from .annotations_tricks import (
    get_Awaitable_arg,
    get_Callable_info,
    get_ClassVar_arg,
    get_ForwardRef_arg,
    get_Iterable_arg,
    get_Iterator_arg,
    get_List_arg,
    get_NewType_arg,
    get_Optional_arg,
    get_Sequence_arg,
    get_Type_arg,
    get_TypeVar_name,
    get_Union_args,
    get_VarTuple_arg,
    is_Any,
    is_Awaitable,
    is_Callable,
    is_ClassVar,
    is_FixedTupleLike_canonical,
    is_ForwardRef,
    is_Iterable,
    is_Iterator,
    is_List,
    is_List_canonical,
    is_NewType,
    is_Optional,
    is_Sequence,
    is_Type,
    is_TypeVar,
    is_Union,
    is_VarTuple,
    is_VarTuple_canonical,
    make_Tuple,
    make_Union,
    make_VarTuple,
)
from .get_patches_ import is_placeholder
from .literal import is_Literal
from .annotations_tricks import (
    CustomList,
    get_CustomList_arg,
    get_DictLike_args,
    get_FixedTupleLike_args,
    get_ListLike_arg,
    get_SetLike_arg,
    is_CustomList,
    is_DictLike,
    is_DictLike_canonical,
    is_FixedTupleLike,
    is_ListLike,
    is_ListLike_canonical,
    is_SetLike,
    is_SetLike_canonical,
    make_dict,
    make_list,
    make_set,
)
from .my_intersection import get_Intersection_args, is_Intersection, make_Intersection
from .uninhabited import is_Uninhabited

__all__ = [
    "get_name_without_brackets",
    "replace_typevars",
    "canonical",
    "NoConstructorImplemented",
    "find_typevars_inside",
]


def get_name_without_brackets(name: str) -> str:
    if "[" in name:
        return name[: name.index("[")]
    else:
        return name


class NoConstructorImplemented(TypeError):
    pass


X = TypeVar("X")


def get_default_attrs():
    from .zeneric2 import dataclass

    @dataclass
    class MyQueue(Generic[X]):
        pass

    return dict(
        Any=Any,
        Optional=Optional,
        Union=Union,
        Tuple=Tuple,
        List=List,
        Set=Set,
        Dict=Dict,
        Queue=MyQueue,
    )


def canonical(typelike: TypeLike) -> TypeLike:
    return replace_typevars(typelike, bindings={}, symbols={}, make_canonical=True)


def replace_typevars(
    cls: TypeLike,
    *,
    bindings: Dict[Any, type],
    symbols: Dict[str, type],
    make_canonical: bool = False,
) -> TypeLike:
    if is_placeholder(cls):
        msg = "Cannot run replace_typevars() on placeholder"
        raise ZValueError(msg, cls=cls)
    r = lambda _: replace_typevars(_, bindings=bindings, symbols=symbols)
    if cls is type:
        return type

    if hasattr(cls, "__name__") and cls.__name__ in symbols:
        return symbols[cls.__name__]
    elif (isinstance(cls, str) or is_TypeVar(cls)) and cls in bindings:
        return bindings[cls]
    elif hasattr(cls, "__name__") and cls.__name__.startswith("Placeholder"):
        return cls
    elif is_TypeVar(cls):
        name = get_TypeVar_name(cls)

        for k, v in bindings.items():
            if is_TypeVar(k) and get_TypeVar_name(k) == name:
                return v
        return cls
        # return bindings[cls]

    elif isinstance(cls, str):
        if cls in symbols:
            return symbols[cls]
        g = dict(get_default_attrs())
        g.update(symbols)
        g0 = dict(g)
        try:
            return eval(cls, g)
        except TypeError as e:
            raise ZTypeError(cls=cls, g=g) from e
        except NameError as e:
            msg = f"Cannot resolve {cls!r}\ng: {list(g0)}"
            # msg += 'symbols: {list(g0)'
            raise NameError(msg) from e
    elif is_NewType(cls):
        # XXX: maybe we should propagate?
        return cls
    elif is_Type(cls):
        x = get_Type_arg(cls)
        r = r(x)
        if x == r:
            return cls
        return Type[r]
        # return type
    elif is_DictLike(cls):
        cls = cast(Type[Dict], cls)
        is_canonical = is_DictLike_canonical(cls)
        K0, V0 = get_DictLike_args(cls)
        K = r(K0)
        V = r(V0)
        # logger.debug(f'{K0} -> {K};  {V0} -> {V}')
        if (K0, V0) == (K, V) and (is_canonical or not make_canonical):
            return cls
        res = make_dict(K, V)
        return res
    elif is_SetLike(cls):
        cls = cast(Type[Set], cls)
        is_canonical = is_SetLike_canonical(cls)
        V0 = get_SetLike_arg(cls)
        V = r(V0)
        if V0 == V and (is_canonical or not make_canonical):
            return cls
        return make_set(V)
    elif is_CustomList(cls):
        cls = cast(Type[CustomList], cls)
        V0 = get_CustomList_arg(cls)
        V = r(V0)
        if V0 == V:
            return cls
        return make_list(V)
    elif is_List(cls):
        cls = cast(Type[List], cls)
        arg = get_List_arg(cls)
        is_canonical = is_List_canonical(cls)
        arg2 = r(arg)
        if arg == arg2 and (is_canonical or not make_canonical):
            return cls
        return List[arg2]
    elif is_ListLike(cls):
        cls = cast(Type[List], cls)
        arg = get_ListLike_arg(cls)
        is_canonical = is_ListLike_canonical(cls)
        arg2 = r(arg)
        if arg == arg2 and (is_canonical or not make_canonical):
            return cls
        return make_list(arg2)
    # XXX NOTE: must go after CustomDict
    elif hasattr(cls, "__annotations__"):
        from .zeneric2 import make_type

        cls2 = make_type(cls, bindings=bindings, symbols=symbols)

        # from zuper_typing.logging_util import ztinfo

        # ztinfo("replace_typevars", bindings=bindings, cls=cls, cls2=cls2)
        # logger.info(f'old cls: {cls.__annotations__}')
        # logger.info(f'new cls2: {cls2.__annotations__}')
        return cls2
    elif is_ClassVar(cls):
        is_canonical = True  # XXXis_ClassVar_canonical(cls)
        x = get_ClassVar_arg(cls)
        r = r(x)
        if x == r and (is_canonical or not make_canonical):
            return cls
        return ClassVar[r]
    elif is_Iterator(cls):
        is_canonical = True  # is_Iterator_canonical(cls)
        # noinspection PyTypeChecker
        x = get_Iterator_arg(cls)
        r = r(x)
        if x == r and (is_canonical or not make_canonical):
            return cls
        return Iterator[r]
    elif is_Sequence(cls):
        is_canonical = True  # is_Sequence_canonical(cls)
        cls = cast(Type[Sequence], cls)

        x = get_Sequence_arg(cls)
        r = r(x)
        if x == r and (is_canonical or not make_canonical):
            return cls

        return Sequence[r]

    elif is_Optional(cls):
        is_canonical = True  # is_Optional_canonical(cls)
        x = get_Optional_arg(cls)
        x2 = r(x)
        if x == x2 and (is_canonical or not make_canonical):
            return cls
        return Optional[x2]

    elif is_Union(cls):
        # cls = cast(Type[Union], cls) cannot cast
        xs = get_Union_args(cls)
        is_canonical = True  # is_Union_canonical(cls)
        ys = tuple(r(_) for _ in xs)
        if ys == xs and (is_canonical or not make_canonical):
            return cls
        return make_Union(*ys)
    elif is_Intersection(cls):
        xs = get_Intersection_args(cls)
        ys = tuple(r(_) for _ in xs)
        if ys == xs:
            return cls
        return make_Intersection(ys)
    elif is_VarTuple(cls):
        cls = cast(Type[Tuple], cls)
        is_canonical = is_VarTuple_canonical(cls)
        X = get_VarTuple_arg(cls)
        Y = r(X)
        if X == Y and (is_canonical or not make_canonical):
            return cls
        return make_VarTuple(Y)
    elif is_FixedTupleLike(cls):
        cls = cast(Type[Tuple], cls)
        is_canonical = is_FixedTupleLike_canonical(cls)
        xs = get_FixedTupleLike_args(cls)
        ys = tuple(r(_) for _ in xs)
        if ys == xs and (is_canonical or not make_canonical):
            return cls
        return make_Tuple(*ys)

    elif is_Callable(cls):
        cinfo = get_Callable_info(cls)

        cinfo2 = cinfo.replace(r)
        return cinfo2.as_callable()
    elif is_Awaitable(cls):
        x = get_Awaitable_arg(cls)
        y = r(x)
        if x == y:
            return cls
        return Awaitable[cls]

    elif is_ForwardRef(cls):
        T = get_ForwardRef_arg(cls)
        if T in symbols:
            return r(symbols[T])
        else:
            logger.warning(f"could not resolve {cls}")
            return cls

    elif cls in (int, bool, float, Decimal, datetime, str, bytes, Number, type(None), object):
        return cls
    elif is_Any(cls):
        return cls
    elif is_Uninhabited(cls):
        return cls
    elif is_Literal(cls):
        return cls

    elif isinstance(cls, type):

        # logger.warning(f"extraneous class {cls}")
        return cls
    # elif is_Literal(cls):
    #     return cls
    else:

        # raise ZNotImplementedError(cls=cls)
        # logger.debug(f"Nothing to do with {cls!r} {cls}")
        return cls


B = Dict[Any, Any]  # bug in Python 3.6


def find_typevars_inside(cls: TypeLike, already: Set[int] = None) -> Tuple[TypeLike, ...]:
    if already is None:
        already = set()
    if id(cls) in already:
        return ()
    already.add(id(cls))
    r = lambda _: find_typevars_inside(_, already)

    def rs(ts):
        res = ()
        for x in ts:
            res = res + r(x)
        return res

    if cls is type:
        return ()
    #
    # if cls is function:
    #     raise ZException(cls=cls, t=type(cls))

    if is_TypeVar(cls):
        return (cls,)
    elif isinstance(cls, str):
        return ()  # XXX
        raise ZNotImplementedError(cls=cls)
        # if cls in symbols:
        #     return symbols[cls]
        # g = dict(get_default_attrs())
        # g.update(symbols)
        # g0 = dict(g)
        # try:
        #     return eval(cls, g)
        # except NameError as e:
        #     msg = f"Cannot resolve {cls!r}\ng: {list(g0)}"
        #     # msg += 'symbols: {list(g0)'
        #     raise NameError(msg) from e
    elif is_NewType(cls):
        return r(get_NewType_arg(cls))
    elif is_Type(cls):
        return r(get_Type_arg(cls))
    elif is_DictLike(cls):
        cls = cast(Type[Dict], cls)
        K0, V0 = get_DictLike_args(cls)
        return r(K0) + r(V0)
    elif is_SetLike(cls):
        cls = cast(Type[Set], cls)
        V0 = get_SetLike_arg(cls)
        return r(V0)
    elif is_ListLike(cls):
        cls = cast(Type[List], cls)
        V0 = get_ListLike_arg(cls)
        return r(V0)
    # XXX NOTE: must go after CustomDict
    elif hasattr(cls, "__annotations__"):
        # from .logging import logger
        #
        # logger.info(cls)
        # logger.info(is_NewType(cls))
        # logger.info(cls.__annotations__)
        d = dict(cls.__annotations__)

        return rs(d.values())
    elif is_ClassVar(cls):
        x = get_ClassVar_arg(cls)
        return r(x)
    elif is_Iterator(cls):
        V0 = get_Iterator_arg(cls)
        return r(V0)
    elif is_Sequence(cls):
        cls = cast(Type[Sequence], cls)
        V0 = get_Sequence_arg(cls)
        return r(V0)
    elif is_Iterable(cls):
        cls = cast(Type[Iterable], cls)
        V0 = get_Iterable_arg(cls)
        return r(V0)
    elif is_Optional(cls):
        x = get_Optional_arg(cls)
        return r(x)
    elif is_Union(cls):
        xs = get_Union_args(cls)
        return rs(xs)
    elif is_Intersection(cls):
        xs = get_Intersection_args(cls)
        return rs(xs)
    elif is_VarTuple(cls):
        cls = cast(Type[Tuple], cls)
        x = get_VarTuple_arg(cls)
        return r(x)
    elif is_FixedTupleLike(cls):
        cls = cast(Type[Tuple], cls)
        xs = get_FixedTupleLike_args(cls)
        return rs(xs)
    elif is_Callable(cls):
        cinfo = get_Callable_info(cls)
        return rs(cinfo.parameters_by_position) + r(cinfo.returns)
    elif is_ForwardRef(cls):
        return ()  # XXX
    elif cls in (int, bool, float, Decimal, datetime, str, bytes, Number, type(None), object):
        return ()
    elif is_Any(cls):
        return ()
    elif is_Uninhabited(cls):
        return ()
    elif is_Literal(cls):
        return ()
    elif isinstance(cls, type):
        return ()
    else:
        raise ZNotImplementedError(cls=cls)
        # logger.debug(f'Nothing to do with {cls!r} {cls}')
        # return cls
