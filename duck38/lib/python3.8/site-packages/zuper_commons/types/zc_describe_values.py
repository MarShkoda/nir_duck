def describe_value(x: object, clip: int = 80) -> str:
    """ Describes an object, for use in the error messages.
        Short description, no multiline.
    """
    if hasattr(x, "shape") and hasattr(x, "dtype"):
        shape_desc = "x".join(str(i) for i in x.shape)
        desc = f"array[{shape_desc!r}]({x.dtype}) "
        final = desc + clipped_repr(x, clip - len(desc))
        return remove_newlines(final)
    else:
        from .zc_describe_type import describe_type

        class_name = describe_type(x)
        desc = f"Instance of {class_name}: "
        final = desc + clipped_repr(x, clip - len(desc))
        return remove_newlines(final)


def clipped_repr(x: object, clip: int) -> str:
    s = repr(x)
    if len(s) > clip:
        clip_tag = "... [clip]"
        cut = clip - len(clip_tag)
        s = f"{s[:cut]}{clip_tag}"
    return s


def remove_newlines(s: str) -> str:
    return s.replace("\n", " ")
