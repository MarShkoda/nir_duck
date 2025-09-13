import time
from contextlib import contextmanager
from logging import Logger
from typing import Callable, Optional, Union

from zuper_commons.logs import ZLogger

__all__ = ["timeit_clock", "timeit_wall"]


class Stack:
    stack = []


@contextmanager
def timeit_generic(
    desc: str, minimum: Optional[float], time_function: Callable[[], float], logger: Union[Logger, ZLogger],
):
    #     logger.debug('timeit %s ...' % desc)

    t0 = time_function()
    try:
        Stack.stack.append(desc)
        yield
    finally:
        Stack.stack.pop()
    t1 = time_function()
    delta = t1 - t0

    if minimum is not None:
        if delta < minimum:
            return

    show_timeit_benchmarks = True
    if show_timeit_benchmarks or (minimum is not None):
        pre = "   " * len(Stack.stack)
        msg = "timeit_clock: %s %6.2f ms  for %s" % (pre, delta * 1000, desc)
        #        t0 = time_function()

        if isinstance(logger, ZLogger):
            logger.info(msg, stacklevel=4)
        else:
            logger.info(msg)


#        t1 = time_function()
#        delta = t1 - t0

try:
    from time import thread_time as measure_thread_time
except ImportError:
    from time import clock as measure_thread_time


@contextmanager
def timeit_clock(desc: Optional[str], logger: Logger, minimum: Optional[float] = None):
    with timeit_generic(desc=desc, minimum=minimum, time_function=measure_thread_time, logger=logger):
        yield


@contextmanager
def timeit_wall(desc: Optional[str], logger: Logger, minimum: Optional[float] = None):
    with timeit_generic(desc=desc, minimum=minimum, time_function=time.time, logger=logger):
        yield
