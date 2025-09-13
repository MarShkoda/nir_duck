import io
import logging
import traceback
from logging import currentframe

from os.path import normcase

__all__ = ["monkeypatch_findCaller"]


def monkeypatch_findCaller():
    if __file__.lower()[-4:] in [".pyc", ".pyo"]:
        _wrapper_srcfile = __file__.lower()[:-4] + ".py"
    else:
        _wrapper_srcfile = __file__
    _wrapper_srcfile = normcase(_wrapper_srcfile)

    def findCaller(self, stack_info=False):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = currentframe()
        # On some versions of IronPython, currentframe() returns None if
        # IronPython isn't run with -X:Frames.
        if f is not None:
            f = f.f_back
        rv = "(unknown file)", 0, "(unknown function)", None
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = normcase(co.co_filename)
            # print(filename)
            if filename == _wrapper_srcfile or filename == logging._srcfile or "zlogger" in filename:
                f = f.f_back
                continue
            sinfo = None
            if stack_info:
                sio = io.StringIO()
                sio.write("Stack (most recent call last):\n")
                traceback.print_stack(f, file=sio)
                sinfo = sio.getvalue()
                if sinfo[-1] == "\n":
                    sinfo = sinfo[:-1]
                sio.close()
            rv = (co.co_filename, f.f_lineno, co.co_name, sinfo)
            break
        # print(rv)
        return rv

    logging.Logger.findCaller = findCaller
