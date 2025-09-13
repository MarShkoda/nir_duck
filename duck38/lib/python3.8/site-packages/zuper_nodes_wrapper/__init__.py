import logging

from zuper_commons.logs import ZLogger

logger = ZLogger(__name__)


logger.setLevel(logging.DEBUG)

logger_interaction = logger.getChild("interaction")
logger_interaction.setLevel(logging.CRITICAL)

from .interface import *
from .struct import *

from .profiler import *
