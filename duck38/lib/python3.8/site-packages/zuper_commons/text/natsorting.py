# -*- coding: utf-8 -*-
import re

# ---------------------------------------------------------
# natsort.py: Natural string sorting.
# ---------------------------------------------------------

# By Seo Sanghyeon.  Some changes by Connelly Barnes.
from typing import Union, List

__all__ = ["natsorted"]


def try_int(s: str) -> Union[str, int]:
    "Convert to integer if possible."
    try:
        return int(s)
    except:
        return s


def natsort_key(s: str):
    "Used internally to get a tuple by which s is sorted."

    s = str(s)  # convert everything to string
    return tuple(map(try_int, re.findall(r"(\d+|\D+)", s)))


def natsorted(seq: List[str]) -> List[str]:
    "Returns a copy of seq, sorted by natural string sort."
    # convert set -> list
    return sorted(list(seq), key=natsort_key)
