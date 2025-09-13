# -*- coding: utf-8 -*-

import pickle

from . import logger
from .types import FilePath
from .zc_debug_pickler import find_pickling_error
from .zc_safe_write import safe_read, safe_write

__all__ = ["safe_pickle_dump", "safe_pickle_load"]

debug_pickling = False


def safe_pickle_dump(
    value: object, filename: FilePath, protocol=3, **safe_write_options,  # pickle.HIGHEST_PROTOCOL,
) -> None:
    # sys.setrecursionlimit(15000)
    with safe_write(filename, **safe_write_options) as f:
        try:
            pickle.dump(value, f, protocol)
        except KeyboardInterrupt:
            raise
        except BaseException:
            msg = f"Cannot pickle object of class {type(value)}."
            logger.error(msg)

            if debug_pickling:
                msg = find_pickling_error(value, protocol)
                logger.error(msg)
            raise


def safe_pickle_load(filename: FilePath) -> object:
    # TODO: add debug check
    with safe_read(filename) as f:
        return pickle.load(f)
        # TODO: add pickling debug
