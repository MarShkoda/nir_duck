__all__ = ["describe_type"]


def describe_type(x: object) -> str:
    """ Returns a friendly description of the type of x. """

    if hasattr(x, "__class__"):
        c = x.__class__
        if hasattr(x, "__name__"):
            class_name = "%s" % c.__name__
        else:
            class_name = str(c)
    else:
        # for extension classes (spmatrix)
        class_name = str(type(x))

    return class_name
