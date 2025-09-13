from typing import Optional as O

from .coloring import get_length_on_screen

__all__ = ["indent"]


def indent(s: str, prefix: str, first: O[str] = None, last: O[str] = None) -> str:
    if not isinstance(s, str):
        s = u"{}".format(s)

    assert isinstance(prefix, str), type(prefix)
    try:
        lines = s.split("\n")
    except UnicodeDecodeError:
        lines = [s]
    if not lines:
        return ""

    if first is None:
        first = prefix
    if last is None:
        couples = [("│", "└"), ("┋", "H")]
        for a, b in couples:
            if a in prefix:
                last = prefix.replace(a, b)
                break
        else:
            last = prefix

    # print(f'{prefix!r:10} -> {get_length_on_screen(prefix)}')
    # print(f'{first!r:10} -> {get_length_on_screen(first)}')
    m = max(get_length_on_screen(prefix), get_length_on_screen(first))

    prefix = " " * (m - get_length_on_screen(prefix)) + prefix
    first = " " * (m - get_length_on_screen(first)) + first
    last = " " * (m - get_length_on_screen(last)) + last

    # differnet first prefix
    res = [u"%s%s" % (prefix, line.rstrip()) for line in lines]
    res[0] = u"%s%s" % (first, lines[0].rstrip())
    return "\n".join(res)
