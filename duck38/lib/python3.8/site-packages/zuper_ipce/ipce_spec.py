from dataclasses import is_dataclass
from typing import Dict, List, overload, Tuple, TypeVar

from zuper_commons.types import ZAssertionError, ZValueError
from .constants import JSONSchema
from .types import IPCE

D = TypeVar("D")

_V = TypeVar("_V")

__all__ = ["assert_canonical_ipce"]


@overload
def sorted_dict_cbor_ord(x: JSONSchema) -> JSONSchema:
    ...


@overload
def sorted_dict_cbor_ord(x: Dict[str, _V]) -> Dict[str, _V]:
    ...


def sorted_dict_cbor_ord(x: Dict[str, _V]) -> Dict[str, _V]:
    if not isinstance(x, dict):
        raise ZAssertionError(x=x)
    res = dict(sorted(x.items(), key=key_dict))

    # TODO
    # assert_sorted_dict_cbor_ord(res)
    return res


def key_dict(item: Tuple[str, object]) -> Tuple[int, str]:
    k, v = item
    return (len(k), k)


def key_list(k: str) -> Tuple[int, str]:
    return (len(k), k)


def sorted_list_cbor_ord(x: List[str]) -> List[str]:
    return sorted(x, key=key_list)


def assert_sorted_dict_cbor_ord(x: dict):
    keys = list(x.keys())
    keys2 = sorted_list_cbor_ord(keys)
    if keys != keys2:
        msg = f"x not sorted"
        raise ZValueError(msg, keys=keys, keys2=keys2)


def assert_canonical_ipce(ob_ipce: IPCE, max_rec=2) -> None:
    IPCL_LINKS = "$links"
    IPCL_SELF = "$self"
    if isinstance(ob_ipce, dict):
        if "/" in ob_ipce:
            msg = 'Cannot have "/" in here '
            raise ZValueError(msg, ob_ipce=ob_ipce)
        assert_sorted_dict_cbor_ord(ob_ipce)

        if IPCL_LINKS in ob_ipce:
            msg = f"Should have dropped the {IPCL_LINKS} part."
            raise ZValueError(msg, ob_ipce=ob_ipce)
        if IPCL_SELF in ob_ipce:
            msg = f"Re-processing the {IPCL_LINKS}."
            raise ZValueError(msg, ob_ipce=ob_ipce)

        for k, v in ob_ipce.items():
            assert not is_dataclass(v), ob_ipce
            if max_rec > 0:
                assert_canonical_ipce(v, max_rec=max_rec - 1)
    elif isinstance(ob_ipce, list):
        pass
    elif isinstance(ob_ipce, tuple):
        msg = "Tuple is not valid."
        raise ZValueError(msg, ob_ipce=ob_ipce)
