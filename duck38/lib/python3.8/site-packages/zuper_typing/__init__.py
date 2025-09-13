__version__ = "6.2.3"

from zuper_commons.logs import ZLogger

logger = ZLogger("typing")
logger.debug(f"version: {__version__}")

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from dataclasses import dataclass

    # noinspection PyUnresolvedReferences
    from typing import Generic

else:
    # noinspection PyUnresolvedReferences
    from .monkey_patching_typing import my_dataclass as dataclass

    # noinspection PyUnresolvedReferences
    from .monkey_patching_typing import ZenericFix as Generic

from .constants import *
from .debug_print_ import *
from .subcheck import *
from .annotations_tricks import *
from .annotations_tricks import *
from .aliases import *
from .get_patches_ import *
from .zeneric2 import *
from .structural_equalities import *
from .literal import *
from .dataclass_info import *
from .my_intersection import *
from .recursive_tricks import *
from .monkey_patching_typing import *
from .assorted_recursive_type_subst import *
from .type_algebra import *
from .uninhabited import *
from .complete import *
from .common import *


resolve_types(CanBeUsed)
