__version__ = "6.1.2"



from zuper_commons.logs import ZLogger

logger = ZLogger(__name__)
import os
path = os.path.dirname(os.path.dirname(__file__))
logger.debug(f'version {__version__} path {path}')

from .types import IPCE, TypeLike
from .constants import IEDO, IESO
from .conv_ipce_from_object import ipce_from_object
from .conv_ipce_from_typelike import ipce_from_typelike
from .conv_object_from_ipce import object_from_ipce
from .conv_typelike_from_ipce import typelike_from_ipce
from .ipce_spec import *

_ = (
    ipce_from_object,
    object_from_ipce,
    typelike_from_ipce,
    ipce_from_typelike,
    TypeLike,
    IPCE,
    IEDO,
    IESO,
)
