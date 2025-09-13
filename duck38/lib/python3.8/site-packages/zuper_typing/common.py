from typing import Any

from .annotations_tricks import make_CustomTuple, make_dict, make_list, make_set

__all__ = [
    "DictStrStr",
    "SetStr",
    "SetObject",
    "DictStrType",
    "DictStrObject",
    "ListStr",
    "DictStrAny",
    "empty_tuple",
    "EmptyTupleType",
    "ListObject",
]

ListObject = make_list(object)
DictStrStr = make_dict(str, str)
DictStrObject = make_dict(str, object)
DictStrAny = make_dict(str, Any)
DictStrType = make_dict(str, type)
SetObject = make_set(object)
SetStr = make_set(str)
ListStr = make_list(str)

EmptyTupleType = make_CustomTuple(())
empty_tuple = EmptyTupleType()
