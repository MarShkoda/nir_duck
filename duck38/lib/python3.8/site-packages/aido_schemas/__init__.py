__version__ = "6.1.1"

from zuper_commons.logs import ZLogger

logger = ZLogger(__name__)
import os

path = os.path.dirname(os.path.dirname(__file__))
logger.debug(f"aido-protocols version {__version__} path {path}")

from .protocols import *
from .protocol_agent import *
from .protocol_simulator import *
from .schemas import *
from .basics import *
from .misc import *
