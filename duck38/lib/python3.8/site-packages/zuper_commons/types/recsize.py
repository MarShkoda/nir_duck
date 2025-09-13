import sys
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Set, Tuple

__all__ = ["get_rec_size"]

from zuper_commons.types import ZException


@dataclass
class RSize:
    nbytes: int = 0
    nobjects: int = 0
    max_size: int = 0
    largest: object = -1
    largest_prefix: Tuple[str, ...] = ()


@dataclass
class RecSize:
    sizes: Dict[type, RSize]


def friendly_mb(s: int) -> str:
    mb = Decimal(s) / Decimal(1024 * 1024)
    mb = mb.quantize(Decimal(".001"))
    return str(mb) + " MB"


def friendly_kb(s: int) -> str:
    mb = Decimal(s) / Decimal(1024)
    mb = mb.quantize(Decimal(".001"))
    return str(mb) + " KB"


def visualize(rs: RecSize, percentile=0.95, min_rows: int = 5) -> str:
    types = list(rs.sizes)
    sizes = list(rs.sizes.values())
    indices = list(range(len(types)))

    # order the indices by size
    def key(i: int) -> int:
        if sizes[i] is object:
            return -1
        return sizes[i].nbytes

    indices = sorted(indices, key=key, reverse=True)

    tot_bytes = rs.sizes[object].nbytes
    stop_at = percentile * tot_bytes
    cells = {}
    row = 0
    so_far = 0
    cells[(row, 0)] = "type"
    cells[(row, 1)] = "# objects"
    cells[(row, 2)] = "bytes"
    cells[(row, 3)] = "max size of 1 ob"
    row += 1
    cells[(row, 0)] = "-"
    cells[(row, 1)] = "-"
    cells[(row, 2)] = "-"
    cells[(row, 3)] = "-"
    row += 1
    for j, i in enumerate(indices):
        Ti = types[i]
        rsi = sizes[i]
        db = ZException.entries_formatter

        cells[(row, 0)] = db(Ti)
        cells[(row, 1)] = db(rsi.nobjects)
        # cells[(row, 2)] = db(rsi.nbytes)
        cells[(row, 2)] = friendly_mb(rsi.nbytes)
        cells[(row, 3)] = friendly_kb(rsi.max_size)
        if Ti in (bytes, str):
            cells[(row, 4)] = "/".join(rsi.largest_prefix)
            cells[(row, 5)] = db(rsi.largest)[:100]
        row += 1
        if Ti is not object:
            so_far += rsi.nbytes
        if j > min_rows and so_far > stop_at:
            break
    from zuper_commons.text import format_table, Style

    align_right = Style(halign="right")
    col_style: Dict[int, Style] = {2: align_right, 3: align_right}
    res = format_table(cells, style="spaces", draw_grid_v=False, col_style=col_style)
    return res


def get_rec_size(ob: object) -> RecSize:
    """Recursively finds size of objects. Traverses mappings and iterables. """

    seen = set()
    sizes = defaultdict(RSize)
    rec_size = RecSize(sizes)
    _get_rec_size(rec_size, ob, seen, ())
    return rec_size


def _get_rec_size(rs: RecSize, obj: object, seen: Set[int], prefix: Tuple[str, ...]) -> None:
    size = sys.getsizeof(obj)

    obj_id = id(obj)
    if obj_id in seen:
        return
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)

    T = type(obj)
    bases = T.__bases__
    Ks = bases + (T,)
    for K in Ks:
        _ = rs.sizes[K]
        _.nbytes += size
        _.nobjects += 1
        if size > _.max_size:
            _.max_size = size
            _.largest = obj
            _.largest_prefix = prefix

    def rec(x: object, p: Tuple[str, ...]):
        _get_rec_size(rs, x, seen, p)

    if isinstance(obj, dict):
        for i, (k, v) in enumerate(obj.items()):
            rec(k, p=prefix + (f"key{i}",))
            rec(v, p=prefix + (f"val{i}",))
    elif hasattr(obj, "__dict__"):
        for k, v in obj.__dict__.items():
            rec(v, p=prefix + (k,))
    elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes, bytearray)):
        # noinspection PyTypeChecker
        for i, v in enumerate(obj):
            rec(v, p=prefix + (str(i),))
