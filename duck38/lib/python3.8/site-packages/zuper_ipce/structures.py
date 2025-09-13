from typing import TypeVar

from zuper_commons.types import ZException
from zuper_typing import dataclass, Generic


class CannotFindSchemaReference(ZException):
    pass


#
# class CannotResolveTypeVar(ZException):
#     pass


KK = TypeVar("KK")
VV = TypeVar("VV")


@dataclass
class FakeValues(Generic[KK, VV]):
    real_key: KK
    value: VV
