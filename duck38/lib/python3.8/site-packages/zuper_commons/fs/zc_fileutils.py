# -*- coding: utf-8 -*-
import codecs
import os
from typing import cast

from zuper_commons.types import check_isinstance

from . import logger
from .types import FilePath
from .zc_friendly_path import friendly_path
from .zc_mkdirs import make_sure_dir_exists
from .zc_path_utils import expand_all

__all__ = [
    "read_bytes_from_file",
    "write_bytes_to_file",
    "read_ustring_from_utf8_file",
    "read_ustring_from_utf8_file_lenient",
    "write_ustring_to_utf8_file",
]


def read_bytes_from_file(filename: FilePath) -> bytes:
    """ Read binary data and returns bytes """
    _check_exists(filename)
    with open(filename, "rb") as f:
        return f.read()


def read_ustring_from_utf8_file(filename: FilePath) -> str:
    """ Returns a unicode/proper string """
    _check_exists(filename)
    with codecs.open(filename, encoding="utf-8") as f:
        try:
            return f.read()
        except UnicodeDecodeError as e:
            msg = f"Could not successfully decode file {filename!r}"
            raise UnicodeError(msg) from e


def read_ustring_from_utf8_file_lenient(filename: FilePath) -> str:
    """ Ignores decoding errors """
    _check_exists(filename)
    with codecs.open(filename, encoding="utf-8", errors="ignore") as f:
        try:
            return f.read()
        except UnicodeDecodeError as e:
            msg = f"Could not successfully decode file {filename!r}"
            raise UnicodeError(msg) from e


def _check_exists(filename: FilePath) -> None:
    if not os.path.exists(filename):
        if os.path.lexists(filename):
            msg = f"The link {filename} does not exist."
            msg += f" it links to {os.readlink(filename)}"
            raise ValueError(msg)
        else:
            msg = f"Could not find file {filename!r}"
            msg += f" from directory {os.getcwd()}"
            raise ValueError(msg)


def write_ustring_to_utf8_file(data: str, filename: FilePath, quiet: bool = False) -> None:
    """
    It also creates the directory if it does not exist.
    :param data:
    :param filename:
    :param quiet:
    :return:
    """
    check_isinstance(data, str)
    b = data.encode("utf-8")  # OK
    return write_bytes_to_file(b, filename, quiet=quiet)


def write_bytes_to_file(data: bytes, filename: FilePath, quiet: bool = False) -> None:
    """
        Writes the data to the given filename.
        If the data did not change, the file is not touched.

    """
    check_isinstance(data, bytes)

    L = len(filename)
    if L > 1024:
        msg = f"Invalid argument filename: too long at {L}. Did you confuse it with data?\n{filename[:1024]}"
        raise ValueError(msg)

    filename = cast(FilePath, expand_all(filename))
    make_sure_dir_exists(filename)

    if os.path.exists(filename):
        with open(filename, "rb") as _:
            current = _.read()
        if current == data:
            if not "assets" in filename:
                if not quiet:
                    logger.debug("already up to date %s" % friendly_path(filename))
            return

    with open(filename, "wb") as f:
        f.write(data)

    if filename.startswith("/tmp"):
        quiet = True

    if not quiet:
        mbs = len(data) / (1024 * 1024)
        size = f"{mbs:.1f}MB"
        logger.debug(f"Written {size} to: {friendly_path(filename)}")
