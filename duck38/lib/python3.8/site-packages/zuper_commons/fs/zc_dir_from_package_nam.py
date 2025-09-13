# -*- coding: utf-8 -*-
import os

from .types import Path

__all__ = ["dir_from_package_name"]


def dir_from_package_name(d: str) -> Path:
    from zuper_commons.text import format_error

    """ This works for "package.sub" format. If it's only
        package, we look for __init__.py"""
    tokens = d.split(".")
    if len(tokens) == 1:
        package = d
        sub = "__init__"
    else:
        package = ".".join(tokens[:-1])
        sub = tokens[-1]
    try:
        from pkg_resources import resource_filename  # @UnresolvedImport

        res = resource_filename(package, sub + ".py")

        if len(tokens) == 1:
            res = os.path.dirname(res)

        return res
    except BaseException as e:  # pragma: no cover
        msg = format_error("Cannot resolve package name", d=d)
        raise ValueError(msg) from e
