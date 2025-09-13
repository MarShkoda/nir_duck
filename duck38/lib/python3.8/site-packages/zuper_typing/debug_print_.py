import inspect
import numbers
from dataclasses import dataclass, field, Field, fields, is_dataclass, replace
from datetime import datetime
from decimal import Decimal
from fractions import Fraction
from typing import Any, Callable, cast, Dict, List, Optional, Sequence, Set, Tuple, Type, TypeVar

import termcolor
from frozendict import frozendict

from zuper_commons.logs import ZLogger
from zuper_commons.text import (
    format_table,
    get_length_on_screen,
    indent,
    remove_escapes,
    Style,
)
from zuper_commons.types import ZException
from zuper_commons.types.exceptions import disable_colored
from zuper_commons.ui import (
    color_constant,
    color_float,
    color_int,
    color_ops,
    color_par,
    color_synthetic_types,
    color_typename,
    color_typename2,
    colorize_rgb,
)
from zuper_commons.ui.colors import color_magenta, color_ops_light
from .aliases import TypeLike
from .annotations_tricks import (
    CustomDict,
    CustomList,
    CustomSet,
    CustomTuple,
    get_Callable_info,
    get_ClassVar_arg,
    get_CustomDict_args,
    get_CustomList_arg,
    get_CustomSet_arg,
    get_CustomTuple_args,
    get_Dict_args,
    get_fields_including_static,
    get_FixedTupleLike_args,
    get_List_arg,
    get_NewType_arg,
    get_NewType_name,
    get_Optional_arg,
    get_Set_arg,
    get_Type_arg,
    get_TypeVar_bound,
    get_Union_args,
    get_VarTuple_arg,
    is_Any,
    is_Callable,
    is_ClassVar,
    is_CustomDict,
    is_CustomList,
    is_CustomSet,
    is_CustomTuple,
    is_Dict,
    is_FixedTupleLike,
    is_ForwardRef,
    is_Iterable,
    is_Iterator,
    is_List,
    is_NewType,
    is_Optional,
    is_Sequence,
    is_Set,
    is_Type,
    is_TypeLike,
    is_TypeVar,
    is_Union,
    is_VarTuple,
    MyBytes,
    MyStr,
    name_for_type_like,
)
from .constants import ATT_PRINT_ORDER, DataclassHooks
from .dataclass_info import has_default_factory, has_default_value
from .literal import get_Literal_args, is_Literal
from .my_intersection import get_Intersection_args, is_Intersection
from .uninhabited import is_Uninhabited
from .zeneric2 import get_dataclass_info

__all__ = [
    "debug_print",
    "DPOptions",
    "debug_print_str",
    "debug_print0",
    "get_default_dpoptions",
]


def nothing(x: object) -> str:
    return ""
    # return " *"


@dataclass
class DPOptions:
    obey_print_order: bool = True
    do_special_EV: bool = True
    do_not_display_defaults: bool = True

    compact: bool = False
    abbreviate: bool = False

    # |│┃┆
    default_border_left = "│ "  # <-- note box-drawing

    id_gen: Callable[[object], object] = id  # cid_if_known
    max_initial_levels: int = 20

    omit_type_if_empty: bool = True
    omit_type_if_short: bool = True

    ignores: List[Tuple[str, str]] = field(default_factory=list)

    other_decoration_dataclass: Callable[[object], str] = nothing

    abbreviate_zuper_lang: bool = False
    ignore_dunder_dunder: bool = False
    spaces_after_separator: bool = True
    preferred_container_width: int = 88

    compact_types: bool = True

    # different_color_mystr : bool = False
    #


def get_default_dpoptions() -> DPOptions:
    ignores = []

    id_gen = id

    return DPOptions(ignores=ignores, id_gen=id_gen)


def remove_color_if_no_support(f):
    def f2(*args, **kwargs):
        s = f(*args, **kwargs)

        if disable_colored():  # pragma: no cover
            s = remove_escapes(s)
        return s

    f2.__name__ = "remove_color_if_no_support"

    return f2


@remove_color_if_no_support
def debug_print(x: object, opt: Optional[DPOptions] = None) -> str:
    if opt is None:
        opt = get_default_dpoptions()
    max_levels = opt.max_initial_levels
    already = {}
    stack = ()
    return debug_print0(x, max_levels=max_levels, already=already, stack=stack, opt=opt)


eop = replace(get_default_dpoptions(), max_initial_levels=20)
ZException.entries_formatter = lambda x: debug_print(x, opt=eop)
eop_log = replace(get_default_dpoptions(), max_initial_levels=5)  # <lower
ZLogger.debug_print = lambda x: debug_print(x, opt=eop_log)


def debug_print0(
    x: object, *, max_levels: int, already: Dict[int, str], stack: Tuple[int, ...], opt: DPOptions
) -> str:
    if id(x) in stack:
        if hasattr(x, "__name__"):
            n = x.__name__
            return color_typename2(n + "↑")  # ↶'
        return "(recursive)"
    if len(stack) > 50:
        return "!!! recursion not detected"
    if opt.compact:
        if isinstance(x, type) and is_dataclass(x):
            other = opt.other_decoration_dataclass(x)
            return color_typename(x.__name__) + other

    # logger.info(f'stack: {stack}  {id(x)} {type(x)}')
    stack2 = stack + (id(x),)
    args = dict(max_levels=max_levels, already=already, stack=stack2, opt=opt)
    dpa = lambda _: debug_print0(_, **args)
    opt_compact = replace(opt, compact=True)
    dp_compact = lambda _: debug_print0(
        _, max_levels=max_levels, already=already, stack=stack2, opt=opt_compact
    )

    # abbreviate = True
    if not opt.abbreviate:
        prefix = ""
    else:
        show_id = is_dataclass(x) and type(x).__name__ != "Constant"
        show_id = True
        if show_id:
            # noinspection PyBroadException
            try:
                h = opt.id_gen(x)
            except:
                prefix = termcolor.colored("!!!", "red")
            # except ValueError:
            #     prefix = '!'
            else:
                if h is not None:
                    if h in already:
                        if isinstance(x, type):
                            short = type(x).__name__ + "(...) "
                        else:
                            short = color_typename(type(x).__name__) + "(...) "
                        res = short + termcolor.colored("$" + already[h], "green")
                        # logger.info(f'ok already[h] = {res} already = {already}')
                        return res
                    else:
                        already[h] = f"{len(already)}"
                        prefix = termcolor.colored("&" + already[h], "green", attrs=["dark"])
                else:
                    prefix = ""
        else:
            prefix = ""

    postfix = " " + prefix if prefix else ""

    if False:  # TODO: make configurable
        postfix += " " + opt.other_decoration_dataclass(x)
        postfix = postfix.rstrip()

    # prefix = prefix + f' L{max_levels}'
    if isinstance(x, int):
        return color_int(str(x)) + postfix

    if isinstance(x, float):
        return color_float(str(x)) + postfix

    if x is type:
        return color_ops("type") + postfix

    if x is BaseException:
        return color_ops("BaseException") + postfix

    if x is tuple:
        return color_ops("tuple") + postfix

    if x is object:
        return color_ops("object") + postfix

    if x is list:
        return color_ops("list") + postfix

    if x is dict:
        return color_ops("dict") + postfix

    if x is type(...):
        return color_ops("ellipsis") + postfix

    if x is int:
        return color_ops("int") + postfix

    if x is float:
        return color_ops("float") + postfix

    if x is bool:
        return color_ops("bool") + postfix

    if x is numbers.Number:
        return color_ops("Number") + postfix
    if x is str:
        return color_ops("str") + postfix

    if x is bytes:
        return color_ops("bytes") + postfix

    if x is set:
        return color_ops("set") + postfix

    if x is slice:
        return color_ops("slice") + postfix

    if x is datetime:
        return color_ops("datetime") + postfix

    if x is Decimal:
        return color_ops("Decimal") + postfix

    if not isinstance(x, str):
        if is_TypeLike(x):
            x = cast(TypeLike, x)
            return debug_print_typelike(x, dp_compact, dpa=dpa, opt=opt, prefix=prefix, args=args)

    if isinstance(x, bytes):
        return debug_print_bytes(x) + postfix

    if isinstance(x, str):
        return debug_print_str(x, prefix=prefix)  # + postfix

    if isinstance(x, Decimal):
        # return color_ops("Dec") + " " + color_float(str(x))
        return color_typename2(str(x))  # + postfix

    if isinstance(x, Fraction):
        if x in known_fraction:
            return color_float(known_fraction[x])  # + postfix
        # return color_ops("Dec") + " " + color_float(str(x))
        return color_float(str(x))  # + postfix

    if isinstance(x, datetime):
        return debug_print_date(x, prefix=prefix)

    if isinstance(x, (set, frozenset)):
        return debug_print_set(x, prefix=prefix, **args)

    if isinstance(x, (dict, frozendict)):
        return debug_print_dict(x, prefix=prefix, **args)

    if isinstance(x, tuple):
        return debug_print_tuple(x, prefix=prefix, **args)

    if isinstance(x, list):
        return debug_print_list(x, prefix=prefix, **args)

    if isinstance(x, (bool, type(None))):
        return color_ops(str(x)) + postfix

    if not isinstance(x, type) and is_dataclass(x):
        return debug_print_dataclass_instance(x, prefix=prefix, **args)

    if "Expr" in type(x).__name__:
        return f"{x!r}\n{x}"

    repr_own = repr(x)
    cname = type(x).__name__
    if cname in repr_own:
        r = repr_own
    else:
        r = f"instance of {cname}: {repr_own}"
    # assert not 'typing.Union' in r, (r, x, is_Union(x))
    return r


known_fraction = {
    Fraction(1, 2): "½",
    Fraction(1, 3): "⅓",
    Fraction(2, 3): "⅔",
    Fraction(1, 4): "¼",
    Fraction(3, 4): "¾",
    Fraction(1, 5): "⅕",
    Fraction(2, 5): "⅖",
    Fraction(3, 5): "⅗",
    Fraction(4, 5): "⅘",
    Fraction(1, 6): "⅙",
    Fraction(5, 6): "⅚",
    Fraction(1, 7): "⅐",
    Fraction(1, 8): "⅛",
    Fraction(3, 8): "⅜",
    Fraction(5, 8): "⅝",
    Fraction(7, 8): "⅞",
    Fraction(1, 9): "⅑",
    Fraction(1, 10): "⅒",
}

cst = color_synthetic_types


def debug_print_typelike(x: TypeLike, dp_compact, dpa, opt: DPOptions, prefix: str, args) -> str:
    h = opt.other_decoration_dataclass(x)

    assert is_TypeLike(x), x
    if is_Any(x):
        s = name_for_type_like(x)
        s = termcolor.colored(s, on_color="on_magenta")
        return s + " " + h
    if is_Uninhabited(x):
        s = "Nothing"
        s = termcolor.colored(s, on_color="on_magenta")
        return s + " " + h
    if is_NewType(x):
        n = get_NewType_name(x)
        w = get_NewType_arg(x)
        return color_synthetic_types(n) + " " + h  # + '<' + debug_print_typelike(w, dpa, opt, '', args)
    if (
        (x is type(None))
        # or is_List(x)
        # or is_Dict(x)
        # or is_Set(x)
        # or is_ClassVar(x)
        # or is_Type(x)
        or is_Iterator(x)
        or is_Sequence(x)
        or is_Iterable(x)
        or is_NewType(x)
        or is_ForwardRef(x)
        or is_Uninhabited(x)
    ):
        s = color_ops(name_for_type_like(x))
        return s + h

    if is_TypeVar(x):
        assert isinstance(x, TypeVar), x

        name = x.__name__

        bound = get_TypeVar_bound(x)
        covariant = getattr(x, "__covariant__")
        contravariant = getattr(x, "__contravariant__")
        if covariant:
            n = name + "+"
        elif contravariant:
            n = name + "-"
        else:
            n = name + "="
        n = cst(n)
        if bound is not object:
            n += color_ops("<") + dp_compact(bound)
        return n + h

    if x is MyBytes:
        s = cst("MyBytes")
        return s + h

    if is_CustomDict(x):
        x = cast(Type[CustomDict], x)
        K, V = get_CustomDict_args(x)
        s = cst("Dict") + cst("[") + dp_compact(K) + cst(",") + dp_compact(V) + cst("]")
        return s + h

    if is_Dict(x):
        x = cast(Type[Dict], x)
        K, V = get_Dict_args(x)
        s = color_ops("Dict") + cst("[") + dp_compact(K) + cst(",") + dp_compact(V) + cst("]")
        return s + h

    if is_Type(x):
        V = get_Type_arg(x)

        s = cst("Type") + cst("[") + dp_compact(V) + cst("]")
        return s + h

    if is_ClassVar(x):
        V = get_ClassVar_arg(x)
        s = color_ops("ClassVar") + cst("[") + dp_compact(V) + cst("]")
        return s + h

    if is_CustomSet(x):
        x = cast(Type[CustomSet], x)
        V = get_CustomSet_arg(x)
        s = cst("Set") + cst("[") + dp_compact(V) + cst("]")
        return s + h

    if is_Set(x):
        x = cast(Type[Set], x)
        V = get_Set_arg(x)
        s = color_ops("Set") + cst("[") + dp_compact(V) + cst("]")
        return s + h

    if is_CustomList(x):
        x = cast(Type[CustomList], x)
        V = get_CustomList_arg(x)
        s = cst("List") + cst("[") + dp_compact(V) + cst("]")
        return s + h

    if is_List(x):
        x = cast(Type[List], x)
        V = get_List_arg(x)
        s = color_ops("List") + cst("[") + dp_compact(V) + cst("]")
        return s + h

    if is_Optional(x):
        V = get_Optional_arg(x)
        s0 = dp_compact(V)
        s = color_ops("Optional") + cst("[") + s0 + cst("]")
        return s + h

    if is_Literal(x):
        vs = get_Literal_args(x)
        s = ", ".join(dp_compact(_) for _ in vs)

        s = color_ops("Literal") + cst("[") + s + cst("]")
        return s + h

    if is_CustomTuple(x):
        x = cast(Type[CustomTuple], x)
        ts = get_CustomTuple_args(x)
        ss = []
        for t in ts:
            ss.append(dp_compact(t))
        args = color_ops(",").join(ss)

        s = cst("Tuple") + cst("[") + args + cst("]")
        return s + h
    if is_FixedTupleLike(x):
        x = cast(Type[Tuple], x)
        ts = get_FixedTupleLike_args(x)
        ss = []
        for t in ts:
            ss.append(dp_compact(t))
        args = color_ops(",").join(ss)
        s = color_ops("Tuple") + cst("[") + args + cst("]")
        return s + h

    if is_VarTuple(x):
        x = cast(Type[Tuple], x)
        t = get_VarTuple_arg(x)
        s = color_ops("Tuple") + cst("[") + dp_compact(t) + ", ..." + cst("]")
        return s + h

    if is_Union(x):
        Ts = get_Union_args(x)

        if opt.compact or len(Ts) <= 3:
            ss = list(dp_compact(v) for v in Ts)
            inside = color_ops(",").join(ss)
            s = color_ops("Union") + cst("[") + inside + cst("]")
        else:
            ss = list(dpa(v) for v in Ts)
            s = color_ops("Union")
            for v in ss:
                s += "\n" + indent(v, "", color_ops(f"* "))
        return s + h

    if is_Intersection(x):
        Ts = get_Intersection_args(x)

        if opt.compact or len(Ts) <= 3:
            ss = list(dp_compact(v) for v in Ts)
            inside = color_ops(",").join(ss)
            s = color_ops("Intersection") + cst("[") + inside + cst("]")
        else:
            ss = list(dpa(v) for v in Ts)
            s = color_ops("Intersection")
            for v in ss:
                s += "\n" + indent(v, "", color_ops(f"* "))
        return s + h

    if is_Callable(x):
        info = get_Callable_info(x)

        def ps(k, v):
            if k.startswith("__"):
                return dp_compact(v)
            else:
                return f"NamedArg({dp_compact(v)},{k!r})"

        params = color_ops(",").join(ps(k, v) for k, v in info.parameters_by_name.items())
        ret = dp_compact(info.returns)
        s = color_ops("Callable") + cst("[[") + params + color_ops("],") + ret + cst("]")
        return s + h

    if isinstance(x, type) and is_dataclass(x):
        if opt.compact_types:
            return name_for_type_like(x)
        else:
            return debug_print_dataclass_type(x, prefix=prefix, **args)

    if hasattr(x, "__name__"):
        n = x.__name__

        if n == "frozendict":
            # return 'frozen' + color_ops('dict')
            return color_ops_light("fdict")
        if n == "frozenset":
            # return 'frozen' + color_ops('set')
            return color_ops_light("fset")

    r = repr(x)
    if "frozendict" in r:
        raise Exception(r)
    r = termcolor.colored(r, "red")
    return r + h


def clipped() -> str:
    return " " + termcolor.colored("...", "blue", on_color="on_yellow")


braces = "{", "}"
empty_dict = "".join(braces)


def debug_print_dict(x: dict, *, prefix, max_levels: int, already: Dict, stack: Tuple[int], opt: DPOptions):
    h = opt.other_decoration_dataclass(x)
    lbrace, rbrace = braces

    if type(x) is frozendict:
        bprefix = "f"
        bracket_colors = color_ops_light
    elif "Dict[" in type(x).__name__:
        bprefix = ""
        bracket_colors = color_synthetic_types
    else:
        bprefix = ""
        bracket_colors = color_ops

    dpa = lambda _: debug_print0(_, max_levels=max_levels - 1, already=already, stack=stack, opt=opt)
    opt_compact = replace(opt, compact=True)
    dps = lambda _: debug_print0(_, max_levels=max_levels, already={}, stack=stack, opt=opt_compact)
    ps = " " + prefix if prefix else ""
    if len(x) == 0:
        if opt.omit_type_if_empty:
            return bracket_colors(bprefix + empty_dict) + ps + " " + h
        else:
            return dps(type(x)) + " " + bracket_colors(bprefix + empty_dict) + ps + " " + h

    s = dps(type(x)) + f"[{len(x)}]" + ps + " " + h
    if max_levels == 0:
        return s + clipped()

    r = {}
    for k, v in x.items():
        if isinstance(k, str):

            if k.startswith("zd"):
                k = "zd..." + k[-4:]
            k = termcolor.colored(k, "yellow")
        else:
            k = dpa(k)
        # ks = debug_print(k)
        # if ks.startswith("'"):
        #     ks = k
        r[k] = dpa(v)

    # colon_sep = ":" + short_space
    colon_sep = ": "
    ss = [k + colon_sep + v for k, v in r.items()]
    nlines = sum(_.count("\n") for _ in ss)
    tlen = sum(get_length_on_screen(_) for _ in ss)
    if nlines == 0 and tlen < get_max_col(stack):
        # x = "," if len(x) == 1 else ""
        res = (
            bracket_colors(bprefix + lbrace)
            + bracket_colors(", ").join(ss)
            + bracket_colors(rbrace)
            + ps
            + " "
            + h
        )

        if opt.omit_type_if_short:
            return res
        else:
            return dps(type(x)) + " " + res

    leftmargin = bracket_colors(opt.default_border_left)
    return pretty_dict_compact(s, r, leftmargin=leftmargin, indent_value=0)


def get_max_col(stack: Tuple) -> int:
    max_line = 110
    return max_line - 4 * len(stack)


def debug_print_dataclass_type(
    x: Type[dataclass], prefix: str, max_levels: int, already: Dict, stack: Tuple, opt: DPOptions
) -> str:
    if max_levels <= 0:
        return name_for_type_like(x) + clipped()

    dpa = lambda _: debug_print0(_, max_levels=max_levels - 1, already=already, stack=stack, opt=opt)
    ps = " " + prefix if prefix else ""

    # ps += f" {id(x)}  {type(x)}" # note breaks string equality
    if opt.abbreviate_zuper_lang:
        if x.__module__.startswith("zuper_lang."):
            return color_constant(x.__name__)
    more = ""
    if x.__name__ != x.__qualname__:
        more += f" ({x.__qualname__})"
    mod = x.__module__ + "."

    s = color_ops("dataclass") + " " + mod + color_typename(x.__name__) + more + ps  # + f' {id(x)}'

    # noinspection PyArgumentList
    other = opt.other_decoration_dataclass(x)
    s += other
    cells = {}
    # FIXME: what was the unique one ?
    seen_fields = set()
    row = 0
    all_fields: Dict[str, Field] = get_fields_including_static(x)
    for name, f in all_fields.items():
        T = f.type
        if opt.ignore_dunder_dunder:
            if f.name.startswith("__"):
                continue

        cells[(row, 0)] = color_ops("field")
        cells[(row, 1)] = f.name
        cells[(row, 2)] = color_ops(":")
        cells[(row, 3)] = dpa(T)

        if has_default_value(f):
            cells[(row, 4)] = color_ops("=")
            cells[(row, 5)] = dpa(f.default)

        elif has_default_factory(f):
            cells[(row, 4)] = color_ops("=")
            cells[(row, 5)] = f"factory {dpa(f.default_factory)}"

        if is_ClassVar(T):
            if not hasattr(x, name):
                cells[(row, 6)] = "no attribute set"
            else:
                v = getattr(x, name)
                # cells[(row, 4)] = color_ops("=")
                cells[(row, 6)] = dpa(v)

        seen_fields.add(f.name)
        row += 1

    try:
        xi = get_dataclass_info(x)
    except:  # pragma: no cover
        cells[(row, 1)] = "cannot get the dataclass info"
        row += 1
    else:
        if xi.orig:
            cells[(row, 1)] = "original"
            cells[(row, 3)] = dpa(xi.orig)
            row += 1

        open = xi.get_open()
        if open:
            cells[(row, 1)] = "open"
            cells[(row, 3)] = dpa(open)
            row += 1

    if getattr(x, "__doc__", None):
        cells[(row, 1)] = "__doc__"
        cells[(row, 3)] = str(getattr(x, "__doc__", "(missing)"))[:50]

    row += 1

    if not cells:
        return s + ": (no fields)"

    align_right = Style(halign="right")
    col_style = {0: align_right, 1: align_right}
    res = format_table(cells, style="spaces", draw_grid_v=False, col_style=col_style)
    return s + "\n" + res  # indent(res, ' ')


list_parens = "[", "]"
# empty_set = "∅"
empty_list = "".join(list_parens)


def debug_print_list(
    x: list, prefix: str, max_levels: int, already: Dict, stack: Tuple, opt: DPOptions
) -> str:
    # if type(x) is frozendict:
    #     bprefix = 'f'
    #     bracket_colors = color_ops_light
    if "List[" in type(x).__name__:
        bracket_colors = color_synthetic_types
    else:
        bracket_colors = color_ops

    lbra, rbra = list_parens
    lbra = bracket_colors(lbra)
    rbra = bracket_colors(rbra)
    empty = bracket_colors(empty_list)

    dpa = lambda _: debug_print0(_, max_levels=max_levels - 1, already=already, stack=stack, opt=opt)
    dps = lambda _: debug_print0(_, opt=opt, max_levels=max_levels, already={}, stack=stack)
    ps = " " + prefix if prefix else ""

    s = dps(type(x)) + f"[{len(x)}]" + ps

    if max_levels <= 0:
        return s + clipped()

    if len(x) == 0:
        if opt.omit_type_if_empty:
            return empty + ps
        else:
            return dps(type(x)) + " " + empty + ps

    ss = [dpa(v) for v in x]
    nlines = sum(_.count("\n") for _ in ss)

    if nlines == 0:
        max_width = min(opt.preferred_container_width, get_max_col(stack))

        sep = color_ops(",")
        if opt.spaces_after_separator:
            sep += " "

        return arrange_in_rows(ss, start=lbra, sep=sep, stop=rbra + ps, max_width=max_width)
    else:
        for i, si in enumerate(ss):
            # s += '\n' + indent(debug_print(v), '', color_ops(f'#{i} '))
            s += "\n" + indent(si, "", color_ops(f"#{i} "))
        return s


def arrange_in_rows(ss: Sequence[str], start: str, sep: str, stop: str, max_width: int) -> str:
    s = start
    indent_length = get_length_on_screen(start)

    cur_line_length = indent_length
    for i, si in enumerate(ss):
        this_one = si

        if i != len(ss) - 1:
            this_one += sep
        this_one_len = get_length_on_screen(this_one)
        if cur_line_length + this_one_len > max_width:
            # s += f' len {cur_line_length}'
            s += "\n"
            s += " " * indent_length
            cur_line_length = indent_length

        s += this_one
        cur_line_length += get_length_on_screen(this_one)
    s += stop
    return s


set_parens = "❨", "❩"
# empty_set = "∅"
empty_set = "".join(set_parens)


def debug_print_set(
    x: set, *, prefix: str, max_levels: int, already: Dict, stack: Tuple, opt: DPOptions
) -> str:
    h = opt.other_decoration_dataclass(x)
    popen, pclose = set_parens

    if type(x) is frozenset:
        bprefix = "f"
        bracket_colors = color_ops_light
    elif "Set[" in type(x).__name__:
        bprefix = ""
        bracket_colors = color_synthetic_types
    else:
        bprefix = ""
        bracket_colors = color_ops

    popen = bracket_colors(bprefix + popen)
    pclose = bracket_colors(pclose)
    dpa = lambda _: debug_print0(_, max_levels=max_levels - 1, already=already, stack=stack, opt=opt)
    dps = lambda _: debug_print0(_, max_levels=max_levels, already={}, stack=stack, opt=opt)

    # prefix = prefix or 'no prefix'
    ps = " " + prefix if prefix else ""

    if len(x) == 0:
        if opt.omit_type_if_empty:
            return bracket_colors(bprefix + empty_set) + ps + " " + h
        else:
            return dps(type(x)) + " " + bracket_colors(bprefix + empty_set) + ps + " " + h

    s = dps(type(x)) + f"[{len(x)}]" + ps + " " + h

    if max_levels <= 0:
        return s + clipped()

    ss = [dpa(v) for v in x]
    nlines = sum(_.count("\n") for _ in ss)
    tlen = sum(get_length_on_screen(_) for _ in ss)
    if nlines == 0 and tlen < get_max_col(stack):
        sep = bracket_colors(",")
        if opt.spaces_after_separator:
            sep += " "
        res = bracket_colors(bprefix + popen) + sep.join(ss) + bracket_colors(pclose) + ps + " " + h
        if opt.omit_type_if_short:
            return res
        else:
            return dps(type(x)) + " " + res

    for i, si in enumerate(ss):
        # s += '\n' + indent(debug_print(v), '', color_ops(f'#{i} '))
        s += "\n" + indent(si, "", bracket_colors("• "))
    return s


# short_space = "\u2009"


tuple_braces = "(", ")"
empty_tuple_str = "".join(tuple_braces)


def debug_print_tuple(
    x: tuple, prefix: str, max_levels: int, already: Dict, stack: Tuple, opt: DPOptions
) -> str:
    dpa = lambda _: debug_print0(_, max_levels=max_levels - 1, already=already, stack=stack, opt=opt)
    dps = lambda _: debug_print0(_, max_levels=max_levels, already={}, stack=stack, opt=opt)
    ps = " " + prefix if prefix else ""

    if "Tuple[" in type(x).__name__:
        bracket_colors = color_synthetic_types
    else:
        bracket_colors = color_ops
    open_brace = bracket_colors(tuple_braces[0])
    close_brace = bracket_colors(tuple_braces[1])

    if len(x) == 0:
        if opt.omit_type_if_empty:
            return bracket_colors(empty_tuple_str) + ps
        else:
            return dps(type(x)) + " " + bracket_colors(empty_tuple_str) + ps

    s = dps(type(x)) + f"[{len(x)}]" + ps

    if max_levels <= 0:
        return s + clipped()

    ss = [dpa(v) for v in x]
    nlines = sum(_.count("\n") for _ in ss)
    tlen = sum(get_length_on_screen(_) for _ in ss)

    if nlines == 0 and tlen < get_max_col(stack):
        x = "," if len(x) == 1 else ""
        sep = bracket_colors(",")
        if opt.spaces_after_separator:
            sep += " "

        res = open_brace + sep.join(ss) + x + close_brace + ps
        if opt.omit_type_if_short:
            return res
        else:
            return dps(type(x)) + " " + res

    for i, si in enumerate(ss):
        s += "\n" + indent(si, "", bracket_colors(f"#{i} "))
    return s


def debug_print_dataclass_instance(
    x: dataclass, prefix: str, max_levels: int, already: Dict, stack: Tuple, opt: DPOptions
) -> str:
    assert is_dataclass(x)
    fields_x = fields(x)
    dpa = lambda _: debug_print0(_, max_levels=max_levels - 1, already=already, stack=stack, opt=opt)
    opt_compact = replace(opt, compact=True)
    dp_compact = lambda _: debug_print0(
        _, max_levels=max_levels - 1, already=already, stack=stack, opt=opt_compact
    )

    # noinspection PyArgumentList
    other = opt.other_decoration_dataclass(x)

    CN = type(x).__name__  # + str(id(type(x)))
    special_colors = {
        "EV": "#77aa77",
        "ZFunction": "#ffffff",
        "ArgRef": "#00ffff",
        "ZArg": "#00ffff",
        "ATypeVar": "#00ffff",
        "MakeProcedure": "#ffffff",
        "IF": "#fafaaf",
    }

    if CN in special_colors:
        cn = colorize_rgb(CN, special_colors[CN])
    else:
        cn = color_typename(CN)

    ps = " " + prefix if prefix else ""
    ps += other
    s = cn + ps

    if max_levels <= 0:
        return s + clipped()

    if opt.obey_print_order and hasattr(x, ATT_PRINT_ORDER):
        options = getattr(x, ATT_PRINT_ORDER)
    else:
        options = []
        for f in fields_x:
            options.append(f.name)

    if opt.do_not_display_defaults:
        same = []
        for f in fields_x:
            att = getattr(x, f.name)
            if has_default_value(f):
                if f.default == att:
                    same.append(f.name)
            elif has_default_factory(f):
                default = f.default_factory()
                if default == att:
                    same.append(f.name)

        to_display = [_ for _ in options if _ not in same]
    else:
        to_display = options
    r = {}
    dpa_result = {}

    for k in to_display:

        if k == "expect":
            att = getattr(x, k)
            # logger.info(f'CN {CN} k {k!r} {getattr(att, "val", None)}')
            if CN == "EV" and k == "expect" and getattr(att, "val", None) is type:
                expects_type = True
                continue

        if not k in to_display:
            continue
        if k.startswith("__"):  # TODO: make configurable
            continue

        if (CN, k) in opt.ignores:
            continue
            # r[color_par(k)] = "(non visualized)"
        else:
            att = getattr(x, k)
            if inspect.ismethod(att):
                att = att()
            r[color_par(k)] = dpa_result[k] = dpa(att)
        # r[(k)] = debug_print(att)

    expects_type = False
    if len(r) == 0:
        return cn + f"()" + prefix + other

    if type(x).__name__ == "Constant":
        s0 = dpa_result["val"]
        if not "\n" in s0:
            # 「 」‹ ›
            return color_constant("⟬") + s0 + color_constant("⟭")
        else:
            l = color_constant("│ ")  # ║")
            f = color_constant("C ")
            return indent(s0, l, f)

    if type(x).__name__ == "QualifiedName":
        module_name = x.module_name
        qual_name = x.qual_name
        return color_typename("QN") + " " + module_name + "." + color_typename(qual_name)

    if type(x).__name__ == "ATypeVar":
        if len(r) == 1:  # only if no other stuff
            return color_synthetic_types(x.typevar_name)

    if CN == "EV" and opt.do_special_EV:

        if len(r) == 1:
            res = list(r.values())[0]
        else:
            res = pretty_dict_compact("", r, leftmargin="")

        if x.pr is not None:
            color_to_use = x.pr.get_color()

        else:
            color_to_use = "#f0f0f0"

        def colorit(_: str) -> str:

            return colorize_rgb(_, color_to_use)

        if expects_type:
            F = "ET "
        else:
            F = "E "
        l = colorit("┋ ")
        f = colorit(F)

        return indent(res, l, f)
    if len(r) == 1:
        k0 = list(r)[0]
        v0 = r[k0]
        if not "\n" in v0 and not "(" in v0:
            return cn + f"({k0}={v0.rstrip()})" + prefix + other
    # ss = list(r.values())
    ss = [k + ": " + v for k, v in r.items()]
    tlen = sum(get_length_on_screen(_) for _ in ss)
    nlines = sum(_.count("\n") for _ in ss)
    # npars = sum(_.count("(") for _ in ss)
    if nlines == 0 and (tlen < get_max_col(stack)) and (tlen < 50):
        # ok, we can do on one line
        if type(x).__name__ == "MakeUnion":
            # assert len(r) == 1 + 1
            ts = x.utypes
            v = [dpa(_) for _ in ts]
            return "(" + color_ops(" ∪ ").join(v) + ")"
        if type(x).__name__ == "MakeIntersection":
            # assert len(r) == 1 + 1
            ts = x.inttypes
            v = [dpa(_) for _ in ts]
            return "(" + color_ops(" ∩ ").join(v) + ")"

        contents = ", ".join(k + "=" + v for k, v in r.items())
        res = cn + "(" + contents + ")" + ps
        return res

    if CN == "MakeProcedure":
        M2 = "┇ "
    else:
        M2 = opt.default_border_left
    if CN in special_colors:
        leftmargin = colorize_rgb(M2, special_colors[CN])
    else:
        leftmargin = color_typename(M2)

    return pretty_dict_compact(s, r, leftmargin=leftmargin, indent_value=0)


#
# def debug_print_dataclass_compact(
#     x, max_levels: int, already: Dict, stack: Tuple,
#     opt: DPOptions
# ):
#     dpa = lambda _: debug_print0(_, max_levels=max_levels - 1, already=already, stack=stack, opt=opt)
#     # dps = lambda _: debug_print(_, max_levels, already={}, stack=stack)
#     s = color_typename(type(x).__name__) + color_par("(")
#     ss = []
#     for k, v in x.__annotations__.items():
#         att = getattr(x, k)
#         ss.append(f'{color_par(k)}{color_par("=")}{dpa(att)}')
#
#     s += color_par(", ").join(ss)
#     s += color_par(")")
#     return s

FANCY_BAR = "│"


def pretty_dict_compact(
    head: Optional[str], d: Dict[str, Any], leftmargin="|", indent_value: int = 0
):  # | <-- note box-making
    if not d:
        return head + ":  (empty dict)" if head else "(empty dict)"
    s = []
    # n = max(get_length_on_screen(str(_)) for _ in d)

    ordered = list(d)
    # ks = sorted(d)
    for k in ordered:
        v = d[k]

        heading = str(k) + ":"
        # if isinstance(v, TypeVar):
        #     # noinspection PyUnresolvedReferences
        #     v = f'TypeVar({v.__name__}, bound={v.__bound__})'
        # if isinstance(v, dict):
        #     v = pretty_dict_compact("", v)

        # vs = v
        if "\n" in v:
            vs = indent(v, " " * indent_value)
            s.append(heading)
            s.append(vs)
        else:
            s.append(heading + " " + v)

        # s.extend(.split('\n'))

    # return (head + ':\n' if head else '') + indent("\n".join(s), '| ')
    indented = indent("\n".join(s), leftmargin)
    return (head + "\n" if head else "") + indented


def nice_str(self):
    return DataclassHooks.dc_repr(self)


def blue(x):
    return termcolor.colored(x, "blue")


def nice_repr(self):
    s = termcolor.colored(type(self).__name__, "red")
    s += blue("(")
    ss = []

    annotations = getattr(type(self), "__annotations__", {})
    for k in annotations:
        if not hasattr(self, k):
            continue
        a = getattr(self, k)
        a_s = debug_print_compact(a)
        eq = blue("=")
        k = termcolor.colored(k, attrs=["dark"])
        ss.append(f"{k}{eq}{a_s}")

    s += blue(", ").join(ss)
    s += blue(")")
    return s


def debug_print_compact(x):
    if isinstance(x, str):
        return debug_print_str(x, prefix="")
    if isinstance(x, bytes):
        return debug_print_bytes(x)
    if isinstance(x, datetime):
        return debug_print_date(x, prefix="")
    return f"{x!r}"


def debug_print_str(x: str, *, prefix: str):
    # Note: this breaks zuper-comp

    different_color_mystr = False
    if different_color_mystr and isinstance(x, MyStr):
        color = color_ops_light
    else:
        color = color_magenta

    if type(x) not in (str, MyStr):
        return type(x).__name__ + " - " + debug_print_str(str(x), prefix=prefix)
    if x == "\n":
        return "'\\n'"
    # if x.startswith("Qm"):
    #     x2 = "Qm..." + x[-4:] + " " + prefix
    #     return termcolor.colored(x2, "magenta")
    # if x.startswith("zd"):
    #     x2 = "zd..." + x[-4:] + " " + prefix
    #     return termcolor.colored(x2, "magenta")
    if x.startswith("-----BEGIN"):
        s = "PEM key" + " " + prefix
        return termcolor.colored(s, "yellow")
    # if x.startswith("Traceback"):
    #     lines = x.split("\n")
    #     colored = [termcolor.colored(_, "red") for _ in lines]
    #     if colored:
    #         colored[0] += "  " + prefix
    #     s = "\n".join(colored)
    #     return s
    ps = " " + prefix if prefix else ""

    lines = x.split("\n")
    if len(lines) > 1:
        first = color("|")
        lines[0] = lines[0] + ps
        try:
            return indent(x, first)
            # res = box(x, color="magenta")  # , attrs=["dark"])
            # return side_by_side([res, ps])
        except:  # pragma: no cover
            # print(traceback.format_exc())
            return "?"

    if x.startswith("zdpu"):
        return termcolor.colored(x, "yellow")

    if x == "":
        return "''"
    else:
        if x.strip() == x:
            return color(x) + ps
        else:
            return color("'" + x + "'") + ps
    # return x.__repr__() + ps


def debug_print_date(x: datetime, *, prefix: str):
    s = x.isoformat()  # [:19]
    s = s.replace("T", " ")
    return termcolor.colored(s, "yellow") + (" " + prefix if prefix else "")


def debug_print_bytes(x: bytes):
    s = f"{len(x)} bytes " + x[:10].__repr__()

    # s = f"{len(x)} bytes " + str(list(x))
    return termcolor.colored(s, "yellow")


DataclassHooks.dc_str = lambda self: debug_print(self)
DataclassHooks.dc_repr = nice_repr
