import re

# escape = re.compile('\x1b\[..?m')

escape = re.compile("\x1b\[[\d;]*?m")

__all__ = ["remove_escapes", "get_length_on_screen"]


def remove_escapes(s):
    return escape.sub("", s)


def get_length_on_screen(s):
    """ Returns the length of s without the escapes """
    return len(remove_escapes(s))
