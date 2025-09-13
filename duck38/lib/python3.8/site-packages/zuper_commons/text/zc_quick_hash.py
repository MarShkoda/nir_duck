import hashlib
from typing import Union

from .types import MD5Hash, SHA1Hash

__all__ = ["get_md5", "get_sha1"]


def get_md5(contents: Union[bytes, str]) -> MD5Hash:
    """ Returns an hexdigest (string).
        If the contents is a string, then it is encoded as utf-8.
    """
    from zuper_commons.types import check_isinstance

    if isinstance(contents, str):
        contents = contents.encode("utf-8")

    check_isinstance(contents, bytes)

    m = hashlib.md5()
    m.update(contents)
    s = m.hexdigest()
    check_isinstance(s, str)
    return MD5Hash(s)


def get_sha1(contents: bytes) -> SHA1Hash:
    from zuper_commons.types import check_isinstance

    """ Returns an hexdigest (string).

     """
    check_isinstance(contents, bytes)
    m = hashlib.sha1()
    m.update(contents)
    s = m.hexdigest()
    check_isinstance(s, str)
    return SHA1Hash(s)
