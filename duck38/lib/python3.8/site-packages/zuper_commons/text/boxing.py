from dataclasses import dataclass
from typing import Optional, List, Tuple

import termcolor

from zuper_commons.text.coloring import get_length_on_screen
from zuper_commons.text.text_sidebyside import pad

__all__ = ["box", "text_dimensions"]


@dataclass
class TextDimensions:
    nlines: int
    max_width: int


def text_dimensions(s: str):
    lines = s.split("\n")
    max_width = max(get_length_on_screen(_) for _ in lines)
    return TextDimensions(nlines=len(lines), max_width=max_width)


#
# U+250x	─	━	│	┃	┄	┅	┆	┇	┈	┉	┊	┋	┌	┍	┎	┏
# U+251x	┐	┑	┒	┓	└	┕	┖	┗	┘	┙	┚	┛	├	┝	┞	┟
# U+252x	┠	┡	┢	┣	┤	┥	┦	┧	┨	┩	┪	┫	┬	┭	┮	┯
# U+253x	┰	┱	┲	┳	┴	┵	┶	┷	┸	┹	┺	┻	┼	┽	┾	┿
# U+254x	╀	╁	╂	╃	╄	╅	╆	╇	╈	╉	╊	╋	╌	╍	╎	╏
# U+255x	═	║	╒	╓	╔	╕	╖	╗	╘	╙	╚	╛	╜	╝	╞	╟
# U+256x	╠	╡	╢	╣	╤	╥	╦	╧	╨	╩	╪	╫	╬	╭	╮	╯
# U+257x	╰	╱	╲	╳	╴	╵	╶	╷	╸	╹	╺	╻	╼	╽	╾	╿

boxes = {
    "pipes": "╔ ═ ╗ ║ ╝ ═ ╚ ║ ╬ ╠ ╣ ╦  ╩ ═ ║ ┼ ╟ ╢ ╤ ╧ ─ │".split(),
    "heavy": "┏ ━ ┓ ┃ ┛ ━ ┗ ┃ ╋ ┣ ┫ ┳  ┻ ━ ┃ ┼ ┠ ┨ ┯ ┷ ─ │".split(),
    "light": "┌ ─ ┐ │ ┘ ─ └ │ ┼ ├ ┤ ┬  ┴ ─ │ ┼ ├ ┤ ┬ ┴ ─ │".split(),
    "circo": "╭ ─ ╮ │ ╯ ─ ╰ │ ┼ ├ ┤ ┬  ┴ ─ │ ┼ ├ ┤ ┬ ┴ ─ │".split(),
}
boxes["spaces"] = [" "] * len(boxes["pipes"])

CORNERS = ["corner"]
NEIGH = ((0, 0, 0), (0, None, 0), (0, 0, 0))


def box(
    s: str,
    style="pipes",
    neighs=NEIGH,
    draw_borders: Tuple[int, int, int, int] = (1, 1, 1, 1),
    light_inside=True,
    color: Optional[str] = None,
    attrs: Optional[List[str]] = None,
    style_fun=None,
) -> str:
    dims = text_dimensions(s)
    padded = pad(s, dims.nlines, dims.max_width, style_fun=style_fun)

    (tl_n, tc_n, tr_n), (ml_n, _, mr_n), (bl_n, bc_n, br_n) = neighs

    S = boxes[style]
    assert len(S) == 22, len(S)
    (
        tl,
        tc,
        tr,
        mr,
        br,
        bc,
        bl,
        ml,
        Pc,
        Pr,
        Pl,
        Pd,
        Pu,
        H,
        V,
        Pc_light,
        Pr_light,
        Pl_light,
        Pd_light,
        Pu_light,
        H_light,
        V_light,
    ) = S

    if light_inside:
        Pc = Pc_light
        Pu = Pu_light
        Pd = Pd_light
        Pr = Pr_light
        Pl = Pl_light
        H = H_light
        V = V_light
    tl_use = {
        (0, 0, 0): tl,
        (0, 0, 1): Pd,
        (0, 1, 0): Pr,
        (0, 1, 1): Pc,  # XXX
        (1, 0, 0): Pc,  # XXX
        (1, 0, 1): Pc,  # XXX
        (1, 1, 0): Pc,
        (1, 1, 1): Pc,
    }[(tl_n, tc_n, ml_n)]

    tr_use = {
        (0, 0, 0): tr,
        (0, 0, 1): Pd,
        (0, 1, 0): Pc,
        (0, 1, 1): Pc,
        (1, 0, 0): Pl,
        (1, 0, 1): Pc,
        (1, 1, 0): Pc,
        (1, 1, 1): Pc,
    }[(tc_n, tr_n, mr_n)]

    br_use = {
        (0, 0, 0): br,
        (0, 0, 1): Pc,
        (0, 1, 0): Pl,
        (0, 1, 1): Pc,
        (1, 0, 0): Pu,
        (1, 0, 1): Pc,
        (1, 1, 0): Pc,
        (1, 1, 1): Pc,
    }[(mr_n, bc_n, br_n)]

    bl_use = {
        (0, 0, 0): bl,
        (0, 0, 1): Pr,
        (0, 1, 0): Pc,
        (0, 1, 1): Pc,
        (1, 0, 0): Pu,
        (1, 0, 1): Pc,
        (1, 1, 0): Pc,
        (1, 1, 1): Pc,
    }[(ml_n, bl_n, bc_n)]

    mr_use = {0: mr, 1: V}[mr_n]
    ml_use = {0: ml, 1: V}[ml_n]
    tc_use = {0: tc, 1: H}[tc_n]
    bc_use = {0: bc, 1: H}[bc_n]

    draw_top, draw_right, draw_bottom, draw_left = draw_borders

    if not draw_right:
        tr_use = ""
        mr_use = ""
        br_use = ""

    if not draw_left:
        tl_use = ""
        ml_use = ""
        bl_use = ""

    top = tl_use + tc_use * dims.max_width + tr_use
    bot = bl_use + bc_use * dims.max_width + br_use

    def f(_):
        if style_fun:
            _ = style_fun(_)
        if color is not None or attrs:
            _ = termcolor.colored(_, color=color, attrs=attrs)
        return _

    top_col = f(top)
    bot_col = f(bot)
    mr_use_col = f(mr_use)
    ml_use_col = f(ml_use)

    new_lines = []
    if draw_top:
        new_lines.append(top_col)
    for l in padded:
        new_lines.append(ml_use_col + l + mr_use_col)

    if draw_bottom:
        new_lines.append(bot_col)
    return "\n".join(new_lines)


# begin = termcolor.colored('║', 'yellow', attrs=['dark'])
# ending = termcolor.colored('║', 'yellow', attrs=['dark'])  # ↵┋
