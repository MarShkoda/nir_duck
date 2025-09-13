import inspect
import logging
from abc import ABC, abstractmethod
from typing import Dict, Union

import termcolor

__all__ = ["ZLogger", "ZLoggerInterface"]


class ZLoggerInterface(ABC):
    @abstractmethod
    def info(self, _msg: str = None, *args, stacklevel: int = 0, **kwargs: object) -> None:
        ...

    @abstractmethod
    def debug(self, _msg: str = None, *args, stacklevel: int = 0, **kwargs: object) -> None:
        ...

    @abstractmethod
    def warn(self, _msg: str = None, *args, stacklevel: int = 0, **kwargs) -> None:
        ...

    @abstractmethod
    def warning(self, _msg: str = None, *args, stacklevel: int = 0, **kwargs) -> None:
        ...

    @abstractmethod
    def error(self, _msg: str = None, *args, stacklevel: int = 0, **kwargs: object) -> None:
        ...

    @abstractmethod
    def getChild(self, child_name: str) -> "ZLoggerInterface":
        ...


class ZLogger(ZLoggerInterface):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARN = logging.WARN
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    logger: logging.Logger
    debug_print = str

    def __init__(self, logger: Union[str, logging.Logger]):
        if isinstance(logger, str):
            logger = logger.replace("zuper_", "")

            logger = logging.getLogger(logger)
            logger.setLevel(logging.DEBUG)
            self.logger = logger
        else:
            self.logger = logger

        from zuper_commons.text import pretty_dict

        self.pretty_dict = pretty_dict
        self.debug_print = None
        # monkeypatch_findCaller()

    def info(self, _msg: str = None, *args, stacklevel: int = 0, **kwargs: object) -> None:
        level = logging.INFO
        return self._log(level=level, msg=_msg, args=args, stacklevel=stacklevel, kwargs=kwargs)

    def debug(self, _msg: str = None, *args, stacklevel: int = 0, **kwargs: object) -> None:
        level = logging.DEBUG
        return self._log(level=level, msg=_msg, args=args, stacklevel=stacklevel, kwargs=kwargs)

    def warn(self, _msg: str = None, *args, stacklevel: int = 0, **kwargs) -> None:
        level = logging.WARN
        return self._log(level=level, msg=_msg, args=args, stacklevel=stacklevel, kwargs=kwargs)

    def warning(self, _msg: str = None, *args, stacklevel: int = 0, **kwargs) -> None:
        level = logging.WARN
        return self._log(level=level, msg=_msg, args=args, stacklevel=stacklevel, kwargs=kwargs)

    def error(self, _msg: str = None, *args, stacklevel: int = 0, **kwargs: object) -> None:
        level = logging.ERROR
        return self._log(level=level, msg=_msg, args=args, stacklevel=stacklevel, kwargs=kwargs)

    def _log(self, level: int, msg: str, args, stacklevel: int, kwargs: Dict[str, object]):
        if self.debug_print is None:
            try:
                # noinspection PyUnresolvedReferences
                from zuper_typing import debug_print

                self.debug_print = debug_print
            except ImportError:
                self.debug_print = str
        if not self.logger.isEnabledFor(level):
            return
        do_inspect = True
        if do_inspect:
            try:
                # 0 is us
                # 1 is one of our methods
                stacklevel += 2
                # for i, frame_i in enumerate(stack[:5]):
                #     x = '***' if i == stacklevel else '   '
                #     print(i, x, frame_i.filename, frame_i.function)
                stack = inspect.stack()
                frame = stack[stacklevel]
                pathname = frame.filename
                lineno = frame.lineno
                funcname = str(frame.function)
                locals = frame[0].f_locals
            except KeyboardInterrupt:
                raise
            except:
                locals = {}
                funcname = "!!!could not inspect()!!!"
                pathname = "!!!"
                lineno = -1
            # print(list(locals))
            if "self" in locals:
                # print(locals['self'])
                typename = locals["self"].__class__.__name__
                funcname = typename + ":" + funcname
        else:
            locals = {}
            funcname = "n/a"
            pathname = "n/a"
            lineno = -1

        res = {}

        def lab(x):
            return x
            # return termcolor.colored(x, attrs=["dark"])

        for i, a in enumerate(args):
            for k, v in locals.items():
                if a is v:
                    use = k
                    break
            else:
                use = str(i)

            res[lab(use)] = ZLogger.debug_print(a)

        for k, v in kwargs.items():
            res[lab(k)] = ZLogger.debug_print(v)

        if res:

            s = self.pretty_dict(msg, res, leftmargin=" ")
            # if not msg:
            #     s = "\n" + s
            # if msg:
            #     s = msg + '\n' + indent(rest, ' ')
            # else:
            #     s = rest
        else:
            s = msg

        # funcname = termcolor.colored(funcname, "red")
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            pathname,
            lineno,
            s,
            (),
            exc_info=None,
            func=funcname,
            extra=None,
            sinfo=None,
        )
        self.logger.handle(record)
        return record
        # self.logger.log(level, s)

    def getChild(self, child_name: str) -> "ZLogger":
        logger_child = self.logger.getChild(child_name)
        return ZLogger(logger_child)

    def setLevel(self, level: int) -> None:
        self.logger.setLevel(level)
