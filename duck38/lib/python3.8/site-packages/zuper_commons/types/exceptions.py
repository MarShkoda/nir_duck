import os
from typing import Callable, ClassVar, Dict, Optional

__all__ = [
    "ZException",
    "ZValueError",
    "ZTypeError",
    "ZAssertionError",
    "ZNotImplementedError",
    "ZKeyError",
]


PASS_THROUGH = (KeyboardInterrupt,)


class ZException(Exception):
    msg: Optional[str] = None
    info: Optional[Dict[str, object]] = None

    entries_formatter: ClassVar[Callable[[object], str]] = repr

    def __init__(self, msg: Optional[str] = None, **info: object):
        self.st = None
        assert isinstance(msg, (str, type(None))), msg
        self.msg = msg
        self.info = info


        # self.__str__()

    def __str__(self) -> str:
        if self.st is None:
            try:
                self.st = self.get_str()
            except PASS_THROUGH:  # pragma: no cover
                raise
            #
            # except BaseException as e:
            #     self.st  = f"!!! could not print: {e}"
        return self.st

    def get_str(self) -> str:

        entries = {}
        for k, v in self.info.items():

            try:
                # noinspection PyCallByClass
                entries[k] = ZException.entries_formatter(v)
            except Exception as e:
                try:
                    entries[k] = f"!!! cannot print: {e}"
                except:
                    entries[k] = f"!!! cannot print, and cannot print exception."
        if not self.msg:
            self.msg = "\n"
        from zuper_commons.text import pretty_dict

        if len(entries) == 1:
            first = list(entries)[0]
            payload = entries[first]
            s = self.msg + f'\n{first}:\n{payload}'

        elif entries:
            s = pretty_dict(self.msg, entries)
        else:
            s = self.msg

        s = sanitize_circle_ci(s)
        return s

    def __repr__(self) -> str:
        return self.__str__()


def disable_colored() -> bool:
    circle_job = os.environ.get("CIRCLE_JOB", None)
    return circle_job is not None


def sanitize_circle_ci(s: str) -> str:
    if disable_colored():
        from zuper_commons.text.coloring import remove_escapes

        s = remove_escapes(s)
        difficult = ["┋"]
        for c in difficult:
            s = s.replace(c, "")
        return s
    else:
        return s


class ZTypeError(ZException, TypeError):
    pass


class ZValueError(ZException, ValueError):
    pass


class ZKeyError(ZException, KeyError):
    pass


class ZAssertionError(ZException, AssertionError):
    pass


class ZNotImplementedError(ZException, NotImplementedError):
    pass
