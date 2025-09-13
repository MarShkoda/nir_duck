from typing import NoReturn, Tuple, Type, Union

from .exceptions import ZValueError

from zuper_commons.text import indent, pretty_msg

__all__ = ["check_isinstance", "raise_wrapped", "raise_desc"]


def check_isinstance(ob: object, expected: Union[type, Tuple[type, ...]], **kwargs: object) -> None:
    if not isinstance(ob, expected):
        kwargs["object"] = ob
        raise_type_mismatch(ob, expected, **kwargs)


def raise_type_mismatch(ob: object, expected: type, **kwargs: object) -> NoReturn:
    """ Raises an exception concerning ob having the wrong type. """
    msg = "Object not of expected type:"
    # e += "\n  expected: {}".format(expected)
    # e += "\n  obtained: {}".format(type(ob))
    # try:
    #     msg = pretty_msg(e, **kwargs)
    # except:
    #     msg = e + "(! cannot write message)"
    raise ZValueError(msg, expected=expected, obtained=type(ob), **kwargs)


def raise_desc(etype: Type[BaseException], msg: str, args_first: bool = False, **kwargs: object) -> NoReturn:
    """

        Example:
            raise_desc(ValueError, "I don't know", a=a, b=b)
    """
    assert isinstance(msg, str), type(msg)
    s1 = msg
    if kwargs:
        s2 = pretty_msg("", **kwargs)
    else:
        s2 = ""

    if args_first:
        s = s2 + "\n" + s1
    else:
        s = s1 + "\n" + s2

    raise etype(s)


def raise_wrapped(
    etype: Type[BaseException], e: BaseException, msg: str, compact: bool = False, **kwargs: object
) -> NoReturn:
    s = pretty_msg(msg, **kwargs)
    if compact:
        s += "\n" + indent(str(e), "| ")
    raise etype(s) from e

    # if not compact:
    #     raise etype(s) from e
    # else:
    #     e2 = etype(s)
    #     raise e2 from e
