# coding=utf-8
import logging
from typing import cast

import termcolor

__all__ = ["setup_logging_color", "setup_logging_format", "setup_logging"]


def get_FORMAT_datefmt():
    pre = "%(asctime)s|%(name)s|%(filename)s:%(lineno)s|%(funcName)s:"
    pre = termcolor.colored(pre, attrs=["dark"])
    FORMAT = pre + "\n" + "%(message)s"
    datefmt = "%H:%M:%S"
    return FORMAT, datefmt


def setup_logging_format():
    from logging import Logger, StreamHandler, Formatter
    import logging

    FORMAT, datefmt = get_FORMAT_datefmt()
    logging.basicConfig(format=FORMAT, datefmt=datefmt)
    # noinspection PyUnresolvedReferences
    root = cast(Logger, Logger.root)
    if root.handlers:
        for handler in root.handlers:
            if isinstance(handler, StreamHandler):
                formatter = Formatter(FORMAT, datefmt=datefmt)
                handler.setFormatter(formatter)
    else:
        logging.basicConfig(format=FORMAT, datefmt=datefmt)


def add_coloring_to_emit_ansi(fn):
    # add methods we need to the class
    from zuper_commons.text import get_length_on_screen
    from zuper_commons.ui.colors import colorize_rgb, get_colorize_function

    RED = "#ff0000"
    GREEN = "#00ff00"
    LGREEN = "#77ff77"
    PINK = "#FFC0CB"
    YELLOW = "#FFFF00"
    colorizers = {
        "red": get_colorize_function(RED),
        "green": get_colorize_function(LGREEN),
        "pink": get_colorize_function(PINK),
        "yellow": get_colorize_function(YELLOW),
        "normal": (lambda x: x),
    }
    prefixes = {
        "red": colorize_rgb(" ", "#000000", bg_color=RED),
        "green": colorize_rgb(" ", "#000000", bg_color=LGREEN),
        "pink": colorize_rgb(" ", "#000000", bg_color=PINK),
        "yellow": colorize_rgb(" ", "#000000", bg_color=YELLOW),
        "normal": " ",
    }

    def new(*args):
        levelno = args[1].levelno
        if levelno >= 50:
            ncolor = "red"
            color = "\x1b[31m"  # red
        elif levelno >= 40:
            ncolor = "red"
            color = "\x1b[31m"  # red
        elif levelno >= 30:
            ncolor = "yellow"
            color = "\x1b[33m"  # yellow
        elif levelno >= 20:
            ncolor = "green"
            color = "\x1b[32m"  # green
        elif levelno >= 10:
            ncolor = "pink"
            color = "\x1b[35m"  # pink
        else:
            ncolor = "normal"
            color = "\x1b[0m"  # normal

        msg = str(args[1].msg)

        lines = msg.split("\n")

        any_color_inside = any(get_length_on_screen(l) != len(l) for l in lines)
        #
        # if any_color_inside:
        #     print(msg.__repr__())

        do_color_lines_inside = False

        def color_line(l):

            if do_color_lines_inside and not any_color_inside:
                return prefixes[ncolor] + " " + colorizers[ncolor](l)
            else:
                return prefixes[ncolor] + " " + l

            # return "%s%s%s" % (color, levelno, "\x1b[0m") + ' ' + l  # normal

        lines = list(map(color_line, lines))
        msg = "\n".join(lines)
        # if len(lines) > 1:
        #     msg = "\n" + msg
        args[1].msg = msg
        return fn(*args)

    return new


def setup_logging_color() -> None:
    import platform

    if platform.system() != "Windows":
        emit1 = logging.StreamHandler.emit
        if getattr(emit1, "__name__", "") != "new":
            emit2 = add_coloring_to_emit_ansi(logging.StreamHandler.emit)
            # print(f'now changing  {logging.StreamHandler.emit} -> {emit2}')
            logging.StreamHandler.emit = emit2


def setup_logging() -> None:
    # logging.basicConfig()
    setup_logging_color()
    setup_logging_format()
