# -*- coding: utf-8 -*-
import os

from .types import Path

__all__ = ["expand_all"]


def expand_all(x0: Path) -> Path:
    x = x0
    x = os.path.expanduser(x)
    x = os.path.expandvars(x)
    if "$" in x:
        msg = "Cannot resolve all environment variables in %r." % x0
        raise ValueError(msg)
    return Path(x)
