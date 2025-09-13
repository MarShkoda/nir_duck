from typing import Mapping, Optional as O, TypeVar

from .coloring import get_length_on_screen
from .zc_indenting import indent

__all__ = ["pretty_dict", "pretty_msg", "format_error"]


def pretty_msg(head: str, **kwargs: object) -> str:
    return pretty_dict(head, kwargs)


format_error = pretty_msg


def pretty_dict(
    head: O[str],
    d: Mapping[str, object],
    omit_falsy: bool = False,
    sort_keys: bool = False,
    leftmargin: str = "│ ",  # | <-- note box-making
) -> str:
    if not d:
        return head + ":  (empty dict)" if head else "(empty dict)"
    s = []
    n = max(get_length_on_screen(str(_)) for _ in d)

    ordered = sorted(d) if sort_keys else list(d)
    # ks = sorted(d)
    for k in ordered:
        v = d[k]

        if k == "__builtins__":
            v = "(hiding __builtins__)"

        if not hasattr(v, "conclusive") and (not isinstance(v, int)) and (not v) and omit_falsy:
            continue
        prefix = (str(k) + ":").rjust(n + 1) + " "

        if isinstance(v, TypeVar):
            # noinspection PyUnresolvedReferences
            v = f"TypeVar({v.__name__}, bound={v.__bound__})"
        if isinstance(v, dict):
            v = pretty_dict("", v)
        s.extend(indent(v, "", prefix).split("\n"))

    # return (head + ':\n' if head else '') + indent("\n".join(s), '| ')
    return (head + "\n" if head else "") + indent("\n".join(s), leftmargin)
