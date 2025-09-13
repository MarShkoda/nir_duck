from typing import Tuple

from .aliases import TypeLike
from .annotations_tricks import is_TypeLike, key_for_sorting_types, name_for_type_like
from .constants import INTERSECTION_ATT, PYTHON_36

__all__ = [
    "get_Intersection_args",
    "make_Intersection",
    "is_Intersection",
    "Intersection",
]

if PYTHON_36:  # pragma: no cover

    class IntersectionMeta(type):
        def __getitem__(self, params):
            return make_Intersection(params)

    class Intersection(metaclass=IntersectionMeta):
        pass


else:

    class Intersection:
        @classmethod
        def __class_getitem__(cls, params):
            # return Intersection_item(cls, params)
            return make_Intersection(params)


class IntersectionCache:
    use_cache = True
    make_intersection_cache = {}


def make_Intersection(ts: Tuple[TypeLike, ...]) -> TypeLike:
    if len(ts) == 0:
        return object
    done = []
    for t in ts:
        assert is_TypeLike(t), ts
        if t not in done:
            done.append(t)

    done = sorted(done, key=key_for_sorting_types)
    ts = tuple(done)
    if len(ts) == 1:
        return ts[0]
    if IntersectionCache.use_cache:
        if ts in IntersectionCache.make_intersection_cache:
            return IntersectionCache.make_intersection_cache[ts]

    class IntersectionBase(type):
        def __eq__(self, other):
            if is_Intersection(other):
                t1 = get_Intersection_args(self)
                t2 = get_Intersection_args(other)
                return set(t1) == set(t2)
            return False

        def __hash__(cls):  # pragma: no cover
            return 1  # XXX
            # logger.debug(f'here ___eq__ {self} {other} {issubclass(other, CustomList)} = {res}')

    attrs = {INTERSECTION_ATT: ts}

    name = "Intersection[%s]" % ",".join(name_for_type_like(_) for _ in ts)

    res = IntersectionBase(name, (), attrs)

    IntersectionCache.make_intersection_cache[ts] = res
    return res


def is_Intersection(T: TypeLike) -> bool:
    return hasattr(T, INTERSECTION_ATT) and type(T).__name__.startswith("Intersection")


def get_Intersection_args(T: TypeLike) -> Tuple[TypeLike, ...]:
    assert is_Intersection(T)
    return getattr(T, INTERSECTION_ATT)
