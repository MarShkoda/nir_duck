from typing import Callable, Optional

import termcolor
import webcolors
from xtermcolor import colorize

__all__ = [
    "color_blue",
    "color_blue_light",
    "color_brown",
    "color_constant",
    "color_float",
    "color_green",
    "color_int",
    "color_ops",
    "color_orange",
    "color_orange_dark",
    "color_par",
    "color_pink",
    "color_synthetic_types",
    "color_pink2",
    "color_typename",
    "color_typename2",
    "colorize_rgb",
    "get_colorize_function",
]

from zuper_commons.types import ZValueError, ZAssertionError

color_orange = "#ffb342"
color_orange_dark = "#cfa342"

color_blue = "#42a0ff"
# color_blue_light = "#62c0ff"
color_blue_light = "#c2a0ff"
color_green = "#42ffa0"
color_pink = "#FF69B4"
color_pink2 = "#FF1493"
color_magenta_1 = "#a000a0"

color_brown = "#b08100"


def colorize_rgb(x: str, rgb: str, bg_color: Optional[str] = None) -> str:
    rgb = interpret_color(rgb)
    bg_color = interpret_color(bg_color)
    if rgb is None:
        msg = "We do not support rgb=None"
        raise ZAssertionError(msg, rgb=rgb, bg_color=bg_color)
    if rgb is None and bg_color is None:
        return x

    fg_int = int(rgb[1:], 16) if rgb is not None else None
    bg_int = int(bg_color[1:], 16) if bg_color is not None else None

    if fg_int is None and bg_int is None:
        return x
    try:
        r = colorize(x, rgb=fg_int, bg=bg_int)
    except Exception as e:
        raise ZValueError(x=x, rgb=rgb, bg_color=bg_color) from e

    if r is None:
        raise NotImplementedError()
    return r


def interpret_color(x: Optional[str]) -> Optional[str]:
    if not x:
        return None
    if x.startswith('#'):
        return x
    return webcolors.name_to_hex(x)


def get_colorize_function(rgb: str, bg_color: Optional[str] = None) -> Callable[[str], str]:
    T = "template"
    Tc = colorize_rgb(T, rgb, bg_color)

    before, _, after = Tc.partition(T)

    def f(s: str) -> str:
        return before + s + after

    return f


color_ops = get_colorize_function(color_blue)
color_ops_light = get_colorize_function(color_blue_light)
color_synthetic_types = get_colorize_function(color_green)
color_int = get_colorize_function(color_pink)
color_float = get_colorize_function(color_pink2)
color_typename = get_colorize_function(color_orange)
color_typename2 = get_colorize_function(color_orange_dark)

color_constant = get_colorize_function(color_pink2)
color_magenta = get_colorize_function(color_magenta_1)


#
# def color_ops(x):
#     return colorize_rgb(x, color_blue)
#
#
# def color_synthetic_types(x):
#     return colorize_rgb(x, color_green)
#
#
# def color_int(x):
#     return colorize_rgb(x, color_pink)
#
#
# def color_float(x):
#     return colorize_rgb(x, color_pink2)
#
#
# def color_typename(x):
#     return colorize_rgb(x, color_orange)


def color_par(x):
    return termcolor.colored(x, attrs=["dark"])
