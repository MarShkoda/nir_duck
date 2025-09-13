import os
from typing import cast

from .types import DirPath, FilePath

__all__ = ["mkdirs_thread_safe", "make_sure_dir_exists"]


def mkdirs_thread_safe(dst: DirPath) -> None:
    """Make directories leading to 'dst' if they don't exist yet"""
    if dst == "" or os.path.exists(dst):
        return
    head, _ = os.path.split(dst)
    if os.sep == ":" and not ":" in head:
        head += ":"
    mkdirs_thread_safe(cast(DirPath, head))
    try:
        os.mkdir(dst, 0o777)
    except OSError as err:
        if err.errno != 17:  # file exists
            raise


def parent_dir(filename: FilePath) -> DirPath:
    d = os.path.dirname(filename)
    return cast(DirPath, d)


def make_sure_dir_exists(filename: FilePath) -> None:
    """ Makes sure that the path to file exists, but creating directories. """
    dirname = parent_dir(filename)
    # dir == '' for current dir
    if dirname != "" and not os.path.exists(dirname):
        mkdirs_thread_safe(dirname)
