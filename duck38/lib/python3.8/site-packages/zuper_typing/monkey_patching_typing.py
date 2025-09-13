import dataclasses
import typing
from dataclasses import dataclass as original_dataclass
from typing import Dict, Generic, Tuple, TypeVar

from zuper_commons.types import ZTypeError
from .annotations_tricks import make_dict
from .constants import ANNOTATIONS_ATT, DataclassHooks, DEPENDS_ATT, PYTHON_36
from .dataclass_info import get_all_annotations
from .zeneric2 import resolve_types, ZenericFix

__all__ = ["get_remembered_class", "MyNamedArg", "remember_created_class", "my_dataclass", "ZenericFix"]


def _cmp_fn_loose(name, op, self_tuple, other_tuple, *args, **kwargs):
    body = [
        "if other.__class__.__name__ == self.__class__.__name__:",
        # "if other is not None:",
        f" return {self_tuple}{op}{other_tuple}",
        "return NotImplemented",
    ]
    fn = dataclasses._create_fn(name, ("self", "other"), body)
    fn.__doc__ = """
    This is a loose comparison function.
    Instead of comparing:

        self.__class__ is other.__class__

    we compare:

        self.__class__.__name__ == other.__class__.__name__

    """
    return fn


dataclasses._cmp_fn = _cmp_fn_loose


def typevar__repr__(self):
    if self.__covariant__:
        prefix = "+"
    elif self.__contravariant__:
        prefix = "-"
    else:
        prefix = "~"
    s = prefix + self.__name__

    if self.__bound__:
        if isinstance(self.__bound__, type):
            b = self.__bound__.__name__
        else:
            b = str(self.__bound__)
        s += f"<{b}"
    return s


setattr(TypeVar, "__repr__", typevar__repr__)

NAME_ARG = "__name_arg__"


# need to have this otherwise it's not possible to say that two types are the same
class Reg:
    already = {}


def MyNamedArg(T, name: str):
    try:
        int(name)
    except:
        pass
    else:
        msg = f"Tried to create NamedArg with name = {name!r}."
        raise ValueError(msg)
    key = f"{T} {name}"
    if key in Reg.already:
        return Reg.already[key]

    class CNamedArg:
        pass

    setattr(CNamedArg, NAME_ARG, name)
    setattr(CNamedArg, "original", T)

    Reg.already[key] = CNamedArg
    return CNamedArg


try:
    import mypy_extensions
except ImportError:
    pass
else:
    setattr(mypy_extensions, "NamedArg", MyNamedArg)


class RegisteredClasses:
    klasses: Dict[Tuple[str, str], type] = {}


def get_remembered_class(module_name: str, qual_name: str) -> type:  # TODO: not tested
    k = (module_name, qual_name)
    return RegisteredClasses.klasses[k]


def remember_created_class(res: type, msg: str = ""):
    k = (res.__module__, res.__qualname__)

    # logger.info(f"Asked to remember {k}: {msg}")
    if k in RegisteredClasses.klasses:
        pass
        # logger.info(f"Asked to remember again {k}: {msg}")
    RegisteredClasses.klasses[k] = res


# noinspection PyShadowingBuiltins
def my_dataclass(_cls=None, *, init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False):
    def wrap(cls):
        # logger.info(f'called my_dataclass for {cls} with bases {_cls.__bases__}')
        # if cls.__name__ == 'B' and len(cls.__bases__) == 1 and cls.__bases__[0].__name__
        # == 'object' and len(cls.__annotations__) != 2:
        #     assert False, (cls, cls.__bases__, cls.__annotations__)
        res = my_dataclass_(
            cls, init=init, repr=repr, eq=eq, order=order, unsafe_hash=unsafe_hash, frozen=frozen
        )
        # logger.info(f'called my_dataclass for {cls} with bases {_cls.__bases__}, '
        #             f'returning {res} with bases {res.__bases__} and annotations {
        #             _cls.__annotations__}')
        remember_created_class(res, "my_dataclass")
        return res

    # See if we're being called as @dataclass or @dataclass().
    if _cls is None:
        # We're called with parens.
        return wrap

    # We're called as @dataclass without parens.
    return wrap(_cls)


# noinspection PyShadowingBuiltins
def my_dataclass_(_cls, *, init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False):
    original_doc = getattr(_cls, "__doc__", None)
    # logger.info(_cls.__dict__)
    unsafe_hash = True

    if hasattr(_cls, "nominal"):
        # logger.info('nominal for {_cls}')
        nominal = True
    else:
        nominal = False
        #

    # if the class does not have a metaclass, add one
    # We copy both annotations and constants. This is needed for cases like:
    #
    #   @dataclass
    #   class C:
    #       a: List[] = field(default_factory=list)
    #
    # #

    if Generic in _cls.__bases__:
        msg = (
            f"There are problems with initialization: class {_cls.__name__} inherits from Generic: "
            f"{_cls.__bases__}"
        )
        raise Exception(msg)

    if type(_cls) is type:
        old_annotations = get_all_annotations(_cls)
        from .zeneric2 import StructuralTyping

        old_annotations.update(getattr(_cls, ANNOTATIONS_ATT, {}))
        attrs = {ANNOTATIONS_ATT: old_annotations}
        for k in old_annotations:
            if hasattr(_cls, k):
                attrs[k] = getattr(_cls, k)

        class Base(metaclass=StructuralTyping):
            pass

        _cls2 = type(_cls.__name__, (_cls, Base) + _cls.__bases__, attrs)

        _cls2.__module__ = _cls.__module__
        _cls2.__qualname__ = _cls.__qualname__
        _cls = _cls2
    else:
        old_annotations = get_all_annotations(_cls)
        old_annotations.update(getattr(_cls, ANNOTATIONS_ATT, {}))

        setattr(_cls, ANNOTATIONS_ATT, old_annotations)

    k = "__" + _cls.__name__.replace("[", "_").replace("]", "_")
    if nominal:
        # # annotations = getattr(K, '__annotations__', {})
        # old_annotations[k] = bool  # typing.Optional[bool]
        old_annotations[k] = typing.ClassVar[bool]  # typing.Optional[bool]
        setattr(_cls, k, True)

    # if True:
    #     anns = getattr(_cls, ANNOTATIONS_ATT)
    #     anns_reordered = reorder_annotations(_cls, anns)
    #     setattr(_cls, ANNOTATIONS_ATT, anns_reordered)

    if "__hash__" in _cls.__dict__:
        unsafe_hash = False
    # print(_cls.__dict__)
    # _cls.__dict__['__hash__']= None
    fields_before = dict(getattr(_cls, dataclasses._FIELDS, {}))
    # if hasattr(_cls, dataclasses._FIELDS):
    #     delattr(_cls, dataclasses._FIELDS)
    try:

        res = original_dataclass(
            _cls, init=init, repr=repr, eq=eq, order=order, unsafe_hash=unsafe_hash, frozen=frozen
        )
    except KeyboardInterrupt:
        raise
    except Exception as e:
        msg = "Cannot create dataclass "
        raise ZTypeError(
            msg,
            _cls=_cls,
            fields=getattr(_cls, dataclasses._FIELDS, "n/a"),
            fields_before=fields_before,
            anns=getattr(_cls, "__annotations__", "n/a"),
        ) from e
    # do it right away
    setattr(res, "__doc__", original_doc)
    # assert dataclasses.is_dataclass(res)
    refs = getattr(_cls, DEPENDS_ATT, ())
    resolve_types(res, refs=refs)

    def __repr__(self) -> str:
        return DataclassHooks.dc_repr(self)

    def __str__(self):
        return DataclassHooks.dc_str(self)

    setattr(res, "__repr__", __repr__)
    setattr(res, "__str__", __str__)

    if nominal:
        setattr(_cls, k, True)  # <!--- FIXME

    return res


if False:

    if PYTHON_36:  # pragma: no cover
        from typing import GenericMeta

        # noinspection PyUnresolvedReferences
        previous_getitem = GenericMeta.__getitem__
    else:
        from typing import _GenericAlias

        previous_getitem = _GenericAlias.__getitem__

    class Alias1:
        def __getitem__(self, params):
            if self is typing.Dict:
                K, V = params
                if K is not str:
                    return make_dict(K, V)

            # noinspection PyArgumentList
            return previous_getitem(self, params)

    def original_dict_getitem(a):
        # noinspection PyArgumentList
        return previous_getitem(Dict, a)

    Dict.__getitem__ = Alias1.__getitem__

    def monkey_patch_dataclass():
        setattr(dataclasses, "dataclass", my_dataclass)

    def monkey_patch_Generic():
        if PYTHON_36:  # pragma: no cover
            GenericMeta.__getitem__ = ZenericFix.__getitem__
        else:
            Generic.__class_getitem__ = ZenericFix.__class_getitem__
            _GenericAlias.__getitem__ = Alias1.__getitem__
