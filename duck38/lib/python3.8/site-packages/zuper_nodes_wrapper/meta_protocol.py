from dataclasses import dataclass

from typing import Any, Dict, List
from zuper_nodes import InteractionProtocol


@dataclass
class SetConfig:
    key: str
    value: Any


@dataclass
class ConfigDescription:
    config: type
    current: Any


@dataclass
class NodeDescription:
    description: str


@dataclass
class BuildDescription:
    pass


@dataclass
class ProtocolDescription:
    data: InteractionProtocol
    meta: InteractionProtocol


@dataclass
class CommsHealth:
    # ignored because not compatible
    ignored: Dict[str, int]
    # unexpected topics
    unexpected: Dict[str, int]
    # malformed data
    malformed: Dict[str, int]
    # if we are completely lost
    unrecoverable_protocol_error: bool


@dataclass
class NodeHealth:
    # there is a critical error that makes it useless to continue
    critical: bool
    # severe problem but we can continue
    severe: bool
    # a minor problem to report
    minor: bool

    details: str


LogEntry = str


basic_protocol = InteractionProtocol(
    description="""\

Basic interaction protocol for nodes spoken by the node wrapper.

    """,
    inputs={
        "describe_config": type(None),
        "set_config": SetConfig,
        "describe_protocol": type(None),
        "describe_node": type(None),
        "describe_build": type(None),
        "get_state": type(None),
        "set_state": Any,
        "get_logs": type(None),
    },
    language="""\
    (
        (in:describe_config ;  out:config_description) |

        (in:set_config      ;  (out:set_config_ack | out:set_config_error)) |

        (in:describe_protocol  ;  out:protocol_description) |

        (in:describe_node   ;  out:node_description) |

        (in:describe_build   ;  out:build_description) |

        (in:get_state   ;  out:node_state) |

        (in:set_state   ;  (out:set_state_ack| out:set_state_error) ) |

        (in:get_logs   ;  out:logs) |

        out:aborted
    )*
""",
    outputs={
        "config_description": ConfigDescription,
        "set_config_ack": type(None),
        "set_config_error": str,
        "protocol_description": ProtocolDescription,
        "node_description": NodeDescription,
        "build_description": BuildDescription,
        "node_state": Any,
        "set_state_ack": type(None),
        "set_state_error": str,
        "logs": List[LogEntry],
        "aborted": str,
    },
)
