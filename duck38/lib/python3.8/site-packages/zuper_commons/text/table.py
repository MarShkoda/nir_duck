import itertools
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple, TypeVar

from .boxing import box, text_dimensions
from .coloring import get_length_on_screen
from .text_sidebyside import pad, side_by_side

try:
    from typing import Literal

    HAlign = Literal["left", "center", "right", "inherit"]
    VAlign = Literal["top", "middle", "bottom", "inherit"]
except ImportError:
    HAlign = VAlign = str

__all__ = ["Style", "format_table", "wrap_lines"]


@dataclass
class Style:
    halign: HAlign = "inherit"
    valign: VAlign = "inherit"
    padding_right: int = "inherit"
    padding_left: int = "inherit"


def format_table(
    cells: Dict[Tuple[int, int], str],
    *,
    draw_grid_v: bool = True,
    draw_grid_h: bool = True,
    style: str = "pipes",
    light_inside: bool = True,
    color: Optional[str] = None,
    attrs: Optional[List[str]] = None,
    col_style: Dict[int, Style] = None,
    row_style: Dict[int, Style] = None,
    cell_style: Dict[Tuple[int, int], Style] = None,
    table_style: Style = None,
    style_fun=None
) -> str:
    """
        Styles: "none", "pipes", ...


    """
    table_style = table_style or Style()
    col_styles = col_style or {}
    row_styles = row_style or {}
    cell_styles = cell_style or {}

    def get_row_style(row: int) -> Style:
        return row_styles.get(row, Style())

    def get_col_style(col: int) -> Style:
        return col_styles.get(col, Style())

    def get_cell_style(cell: Tuple[int, int]) -> Style:
        return cell_styles.get(cell, Style())

    X = TypeVar("X")

    def resolve(a: List[X]) -> X:
        cur = a[0]
        for _ in a:
            if _ == "inherit":
                continue
            else:
                cur = _
        return cur

    def get_style(cell: Tuple[int, int]) -> Style:
        row, col = cell
        rows = get_row_style(row)
        cols = get_col_style(col)
        cels = get_cell_style(cell)
        halign = resolve(["left", table_style.halign, rows.halign, cols.halign, cels.halign])
        valign = resolve(["top", table_style.valign, rows.valign, cols.valign, cels.valign])
        padding_left = resolve(
            [0, table_style.padding_left, rows.padding_left, cols.padding_left, cels.padding_left]
        )
        padding_right = resolve(
            [0, table_style.padding_right, rows.padding_right, cols.padding_right, cels.padding_right]
        )
        return Style(halign=halign, valign=valign, padding_left=padding_left, padding_right=padding_right)

    cells = dict(cells)
    # find all mentioned cells
    mentioned_js = set()
    mentioned_is = set()

    for i, j in cells:
        mentioned_is.add(i)
        mentioned_js.add(j)

    # add default = '' for missing cells
    nrows = max(mentioned_is) + 1 if mentioned_is else 1
    ncols = max(mentioned_js) + 1 if mentioned_js else 1
    coords = list(itertools.product(range(nrows), range(ncols)))
    for c in coords:
        if c not in cells:
            cells[c] = ""

    # find max size for cells
    row_heights = [0] * nrows
    col_widths = [0] * ncols
    for (i, j), s in list(cells.items()):
        dims = text_dimensions(s)
        col_widths[j] = max(col_widths[j], dims.max_width)
        row_heights[i] = max(row_heights[i], dims.nlines)

    # pad all cells
    for (i, j), s in list(cells.items()):
        linelength = col_widths[j]
        nlines = row_heights[i]

        cell_style = get_style((i, j))

        padded = do_padding(
            s,
            linelength=linelength,
            nlines=nlines,
            halign=cell_style.halign,
            valign=cell_style.valign,
            padding_left=cell_style.padding_left,
            padding_right=cell_style.padding_right,
            style_fun=style_fun,
        )
        ibef = int(i > 0)
        iaft = int(i < nrows - 1)
        jbef = int(j > 0)
        jaft = int(j < ncols - 1)

        neighs = (
            (ibef * jbef, ibef, ibef * jaft),
            (jbef, None, jaft),
            (iaft * jbef, iaft, iaft * jaft),
        )

        draw_top = 1
        draw_left = 1
        draw_right = jaft == 0
        draw_bottom = iaft == 0

        if not draw_grid_v:
            draw_bottom = draw_top = 0
        if not draw_grid_h:
            draw_left = draw_right = 0
        d = draw_top, draw_right, draw_bottom, draw_left

        if style == "none":
            s = " " + padded
        else:
            s = box(
                padded,
                neighs=neighs,
                style=style,
                draw_borders=d,
                light_inside=light_inside,
                color=color,
                attrs=attrs,
                style_fun=style_fun,
            )

        cells[(i, j)] = s

    parts = []
    for i in range(nrows):
        ss = []
        for j in range(ncols):
            ss.append(cells[(i, j)])
        s = side_by_side(ss, sep="")
        parts.append(s)

    whole = "\n".join(parts)
    # res = box(whole, style=style)
    # logger.info(f'table {cells!r}')
    return whole


def wrap_lines(s: str, max_width: int):
    lines = s.split("\n")
    res = []

    while lines:
        l = lines.pop(0)
        n = get_length_on_screen(l)
        if n <= max_width:
            res.append(l)
        else:
            a = l[:max_width]
            b = "$" + l[max_width:]
            res.append(a)
            lines.insert(0, b)

    return "\n".join(res)


def do_padding(
    s: str,
    linelength: int,
    nlines: int,
    halign: HAlign,
    valign: VAlign,
    padding_left: int,
    padding_right: int,
    style_fun: Callable[[str], str] = None,
    pad_char=" ",
) -> str:
    padded_lines = pad(
        s, linelength=linelength, nlines=nlines, halign=halign, valign=valign, style_fun=style_fun
    )
    pl = pad_char * padding_left
    pr = pad_char * padding_right
    if style_fun is not None:
        pl = style_fun(pl)
        pr = style_fun(pr)
    padded_lines = [pl + _ + pr for _ in padded_lines]

    padded = "\n".join(padded_lines)

    return padded
