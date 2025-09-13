from typing import NewType

__all__ = ["MarkdownStr", "MD5Hash", "SHA1Hash", "HTMLString", "XMLString", "JSONString"]

MarkdownStr = str
""" A Markdown string """

MD5Hash = NewType("MD5Hash", str)
""" A MD5 hash"""

SHA1Hash = NewType("SHA1Hash", str)
""" A SHA-1 hash"""

HTMLString = str
""" A string containing HTML """

XMLString = str
""" A string containing XML """

JSONString = NewType("JSONString", str)
""" A string containing JSON """
