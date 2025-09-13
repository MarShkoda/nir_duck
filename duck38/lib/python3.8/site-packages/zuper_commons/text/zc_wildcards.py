# -*- coding: utf-8 -*-

import re
from typing import Iterator, List, Sequence, Union

__all__ = ["expand_string", "get_wildcard_matches", "wildcard_to_regexp", 'expand_wildcard']


def flatten(seq: Iterator) -> List:
    res = []
    for l in seq:
        res.extend(l)
    return res


def expand_string(x: Union[str, Sequence[str]], options: Sequence[str]) -> List[str]:
    if isinstance(x, list):
        return flatten(expand_string(y, options) for y in x)
    elif isinstance(x, str):
        x = x.strip()
        if "," in x:
            splat = [_ for _ in x.split(",") if _]  # remove empty
            return flatten(expand_string(y, options) for y in splat)
        elif "*" in x:
            xx = expand_wildcard(x, options)
            expanded = list(xx)
            return expanded
        else:
            return [x]
    else:
        assert False, x


def wildcard_to_regexp(arg: str):
    """ Returns a regular expression from a shell wildcard expression. """
    return re.compile("\A" + arg.replace("*", ".*") + "\Z")


def has_wildcard(s: str) -> bool:
    return s.find("*") > -1


def expand_wildcard(wildcard: str, universe: Sequence[str]) -> Sequence[str]:
    """
        Expands a wildcard expression against the given list.
        Raises ValueError if none found.

        :param wildcard: string with '*'
        :param universe: a list of strings
    """
    if not has_wildcard(wildcard):
        msg = "No wildcards in %r." % wildcard
        raise ValueError(msg)

    matches = list(get_wildcard_matches(wildcard, universe))

    if not matches:
        msg = "Could not find matches for pattern %r in %s." % (wildcard, universe)
        raise ValueError(msg)

    return matches


def get_wildcard_matches(wildcard: str, universe: Sequence[str]) -> Iterator[str]:
    """
        Expands a wildcard expression against the given list.
        Yields a sequence of strings.

        :param wildcard: string with '*'
        :param universe: a list of strings
    """
    regexp = wildcard_to_regexp(wildcard)
    for x in universe:
        if regexp.match(x):
            yield x
