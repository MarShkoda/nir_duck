import socket
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np

__all__ = [
    "AIDONodesException",
    "ProtocolViolation",
    "ExternalProtocolViolation",
    "InternalProtocolViolation",
    "DecodingError",
    "EncodingError",
    "Timestamp",
    "timestamp_from_seconds",
    "TimeSpec",
    "local_time",
    "TimingInfo",
    # "EnvironmentError",
    "NotConforming",
    "ExternalTimeout",
    "ExternalNodeDidNotUnderstand",
    "RemoteNodeAborted",
    "InternalProblem",
]


class AIDONodesException(Exception):
    pass


class ProtocolViolation(AIDONodesException):
    pass


class ExternalProtocolViolation(ProtocolViolation):
    pass


class ExternalNodeDidNotUnderstand(ExternalProtocolViolation):
    pass


class RemoteNodeAborted(ExternalProtocolViolation):
    pass


class ExternalTimeout(ExternalProtocolViolation):
    pass


class InternalProblem(AIDONodesException):
    pass


class InternalProtocolViolation(ProtocolViolation):
    pass


class DecodingError(AIDONodesException):
    pass


class EncodingError(AIDONodesException):
    pass


class NotConforming(AIDONodesException):
    """ The node is not conforming to the protocol. """

    pass


#
#
# class EnvironmentError(AIDONodesException):
#     """ Things such as files not existing. """
#
#     pass


@dataclass
class Timestamp:
    s: int
    us: int


def timestamp_from_seconds(f: float) -> Timestamp:
    s = int(np.floor(f))
    extra = f - s
    us = int(extra * 1000 * 1000 * 1000)
    return Timestamp(s, us)


@dataclass
class TimeSpec:
    time: Timestamp
    frame: str
    clock: str

    time2: Optional[Timestamp] = None


def local_time() -> TimeSpec:
    s = time.time()
    hostname = socket.gethostname()
    return TimeSpec(time=timestamp_from_seconds(s), frame="epoch", clock=hostname)


@dataclass
class TimingInfo:
    acquired: Optional[Dict[str, TimeSpec]] = field(default_factory=dict)
    processed: Optional[Dict[str, TimeSpec]] = field(default_factory=dict)
    received: Optional[TimeSpec] = None
