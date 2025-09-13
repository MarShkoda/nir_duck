from dataclasses import dataclass, Field, fields, is_dataclass, MISSING
from typing import Dict, Optional, Tuple, Type

from zuper_commons.text import pretty_dict
from zuper_commons.types import ZAssertionError, ZValueError
from . import logger
from .aliases import TypeLike
from .annotations_tricks import is_TypeLike
from .constants import ANNOTATIONS_ATT

from .constants import MULTI_ATT

__all__ = [
    "get_dataclass_info",
    "set_dataclass_info",
    "DataclassInfo",
    "same_as_default",
    "is_dataclass_instance",
    "asdict_not_recursive",
    "has_default",
    "get_default",
    "get_fields_values",
]


class DataclassInfo:
    name: str  # only for keeping track
    # These are the open ones
    # generic_att_XXX: Tuple[TypeLike, ...]
    # These are the bound ones
    # bindings: Dict[TypeLike, TypeLike]
    # These are the original ones
    orig: Tuple[TypeLike, ...]

    # Plus the ones we collected
    # extra: Tuple[TypeLike, ...]
    specializations: Dict[Tuple, type]
    _open: Optional[Tuple[TypeLike, ...]]

    fti = None

    def __init__(self, *, name: str, orig: Tuple[TypeLike, ...]):
        self.name = name
        # self.bindings = bindings
        self.orig = orig
        if not isinstance(orig, tuple):  # pragma: no cover
            raise ZAssertionError(sself=self)
        for i, _ in enumerate(orig):  # pragma: no cover
            if not is_TypeLike(_):
                msg = f"Element #{i} is not a typelike."
                raise ZAssertionError(msg, name=name, orig=orig)
        # self.extra = extra
        # if bindings: raise ZException(self=self)
        self.specializations = {}
        self._open = None

    def get_open(self) -> Tuple[TypeLike, ...]:
        if DataclassInfo.fti is None:
            from .recursive_tricks import find_typevars_inside

            DataclassInfo.fti = find_typevars_inside

        _open = getattr(self, "_open", None)
        if _open is None:
            res = []
            for x in self.orig:
                for y in DataclassInfo.fti(x):
                    if y not in res:
                        res.append(y)
            self._open = tuple(res)

        return self._open

    #
    # def get_open_old(self) -> Tuple[TypeLike, ...]:
    #     res = []
    #     for x in self.orig:
    #           if x not in self.bindings:
    #             res.append(x)
    #     for x in self.extra:
    #         if x not in self.bindings:
    #             res.append(x)
    #
    #     return tuple(res)

    # def __post_init__(self):
    #     for k in self.bindings:
    #         if k not in (self.orig + self.extra):
    #             msg = f"There is a bound variable {k} which is not an original one or child. "
    #             raise ZValueError(msg, di=self)

    def __repr__(self):
        # from .debug_print_ import debug_print
        debug_print = str
        return pretty_dict(
            "DataclassInfo",
            dict(
                name=self.name,
                orig=debug_print(self.orig),
                # extra=debug_print(self.extra),
                # bindings=debug_print(self.bindings)
                open=self.get_open(),
            ),
        )


def set_dataclass_info(T, di: DataclassInfo):
    assert is_TypeLike(T), T
    if not hasattr(T, MULTI_ATT):
        setattr(T, MULTI_ATT, {})
    ma = getattr(T, MULTI_ATT)

    ma[id(T)] = di


def get_dataclass_info(T: Type[dataclass]) -> DataclassInfo:
    assert is_TypeLike(T), T
    default = DataclassInfo(name=T.__name__, orig=())
    if not hasattr(T, MULTI_ATT):
        return default
    ma = getattr(T, MULTI_ATT)
    if not id(T) in ma:
        msg = f"Cannot find type info for {T} ({id(T)}"
        logger.info(msg, ma=ma)
        return default
    return ma[id(T)]


def get_fields_values(x: dataclass) -> Dict[str, object]:
    assert is_dataclass_instance(x), x
    res = {}
    T = type(x)
    try:
        fields_ = fields(T)
    except Exception as e:
        raise ZValueError(T=T) from e
    for f in fields_:
        k = f.name
        v0 = getattr(x, k)
        res[k] = v0
    return res


def get_all_annotations(cls: type) -> Dict[str, type]:
    """ Gets all the annotations including the parents. """
    res = {}
    for base in cls.__bases__:
        annotations = getattr(base, ANNOTATIONS_ATT, {})
        res.update(annotations)

    return res


def asdict_not_recursive(x: dataclass) -> Dict[str, object]:
    """ Note: this does not return  the classvars"""
    return get_fields_values(x)


def is_dataclass_instance(x: object) -> bool:
    return not isinstance(x, type) and is_dataclass(x)


def has_default(f: Field):
    """ Returns true if it has a default value or factory"""
    if f.default != MISSING:
        return True
    elif f.default_factory != MISSING:
        return True
    else:
        return False


def has_default_value(f: Field):
    if f.default != MISSING:
        return True
    else:
        return False


def has_default_factory(f: Field):
    if f.default_factory != MISSING:
        return True
    else:
        return False


def get_default(f: Field) -> object:
    assert has_default(f)
    if f.default != MISSING:
        return f.default
    elif f.default_factory != MISSING:
        return f.default_factory()
    assert False


def same_as_default(f: Field, value: object) -> bool:
    if f.default != MISSING:
        return f.default == value
    elif f.default_factory != MISSING:
        default = f.default_factory()
        return default == value
    else:
        return False
