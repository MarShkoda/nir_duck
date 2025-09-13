from functools import wraps
from typing import Tuple
from unittest import SkipTest

from nose.plugins.attrib import attr

from ..types import ZValueError, ZAssertionError

__all__ = ["known_failure", "relies_on_missing_features", "my_assert_equal"]


def known_failure(f, forbid: Tuple[type, ...] = ()):  # pragma: no cover
    @wraps(f)
    def run_test(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except BaseException as e:

            if forbid:
                if isinstance(e, forbid):
                    msg = f"Known failure test is not supposed to raise {type(e).__name__}"
                    raise AssertionError(msg) from e

            raise SkipTest("Known failure test failed: " + str(e))
        raise AssertionError("test passed but marked as work in progress")

    return attr("known_failure")(run_test)


def relies_on_missing_features(f):
    msg = "Test relying on not implemented feature."

    @wraps(f)
    def run_test(*args, **kwargs):  # pragma: no cover
        try:
            f(*args, **kwargs)
        except BaseException as e:
            raise SkipTest(msg) from e
        raise AssertionError("test passed but marked as work in progress")

    return attr("relies_on_missing_features")(run_test)


def my_assert_equal(a, b, msg=None):
    if a != b:
        m = "Not equal"
        if msg is not None:
            m += ": " + msg
        raise ZValueError(m, a=a, b=b)


def assert_isinstance(a, C):
    if not isinstance(a, C):  # pragma: no cover
        raise ZAssertionError(
            "not isinstance", a=a, type_a=type(a), type_type_a=type(type(a)), C=C, type_C=type(C),
        )


def assert_issubclass(A, C):
    if not issubclass(A, C):  # pragma: no cover
        raise ZAssertionError("not issubclass", A=A, C=C, type_A=type(A), type_C=type(C))
