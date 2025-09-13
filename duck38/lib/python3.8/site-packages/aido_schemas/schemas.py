from typing import Dict, TYPE_CHECKING

import numpy as np

from zuper_nodes import particularize_no_check

if TYPE_CHECKING:
    from dataclasses import dataclass
else:
    from zuper_typing import dataclass

from .protocol_agent import protocol_agent
from .protocol_simulator import (
    DuckieState,
    JPGImage,
    JPGImageWithTimestamp,
    protocol_simulator,
    RobotName,
    RobotObservations,
    RobotState,
    SetRobotCommands,
    StateDump,
)

__all__ = [
    "PWMCommands",
    "Duckiebot1Observations",
    "Duckiebot1ObservationsPlusState",
    "Duckiebot1Commands",
    "LEDSCommands",
    "RGB",
    "DB18SetRobotCommands",
    "DB18RobotObservations",
    "protocol_agent_duckiebot1",
    "protocol_simulator_duckiebot1",
    "protocol_agent_duckiebot1_fullstate",
    "DTSimRobotInfo",
    "DTSimRobotState",
    "DTSimState",
    "DTSimStateDump",
    "DB20Observations",
    "DB20Commands",
    "DB20Odometry",
    "DB20ObservationsPlusState",
    "DB20RobotObservations",
    "DB20SetRobotCommands",
    "protocol_agent_DB20",
    "protocol_agent_DB20_fullstate",
    "protocol_simulator_DB20",
    "DTSimDuckieInfo",
    "DTSimDuckieState",
    "DB20ObservationsOnlyState",
    "protocol_agent_DB20_onlystate",
    "DB20ObservationsOnlyState",
    "protocol_agent_DB20_timestamps",
    "protocol_simulator_DB20_timestamps",
    "DB20ObservationsWithTimestamp",
    "DB20OdometryWithTimestamp",
    "DB20RobotObservationsWithTimestamp",
]


@dataclass
class PWMCommands:
    """
    PWM commands are floats between -1 and 1.
    """

    motor_left: float
    motor_right: float

    def __post_init__(self):
        self.motor_left = float(self.motor_left)
        self.motor_right = float(self.motor_right)
        m = max(abs(self.motor_left), abs(self.motor_right))
        if m > 1:
            msg = f"Expected values to be between -1 and 1. Obtained {self.motor_left}, {self.motor_right}"
            raise ValueError(msg)


@dataclass
class Duckiebot1Observations:
    camera: JPGImage


@dataclass
class RGB:
    """Values between 0, 1."""

    r: float
    g: float
    b: float

    def __post_init__(self):
        for a in [self.r, self.g, self.b]:
            if not isinstance(a, float):
                raise ValueError(a)


@dataclass
class LEDSCommands:
    center: RGB
    front_left: RGB
    front_right: RGB
    back_left: RGB
    back_right: RGB


@dataclass
class Duckiebot1Commands:
    wheels: PWMCommands
    LEDS: LEDSCommands


@dataclass
class DB18SetRobotCommands(SetRobotCommands):
    robot_name: RobotName
    t_effective: float
    commands: Duckiebot1Commands


@dataclass
class DB18RobotObservations(RobotObservations):
    robot_name: RobotName
    t_effective: float
    observations: Duckiebot1Observations


@dataclass
class DTSimRobotInfo:
    pose: np.ndarray
    velocity: np.ndarray
    pwm: PWMCommands
    leds: LEDSCommands


@dataclass
class DTSimRobotState(RobotState):
    robot_name: RobotName
    t_effective: float
    state: DTSimRobotInfo


@dataclass
class DTSimDuckieInfo:
    pose: np.ndarray
    velocity: np.ndarray


@dataclass
class DTSimDuckieState(DuckieState):
    duckie_name: RobotName
    t_effective: float
    state: DTSimDuckieInfo


@dataclass
class DTSetMap:
    map_data: str


@dataclass
class DTSimState:
    t_effective: float
    duckiebots: Dict[str, DTSimRobotInfo]
    duckies: Dict[str, DTSimDuckieInfo]


@dataclass
class DTSimStateDump(StateDump):
    state: DTSimState


@dataclass
class Duckiebot1ObservationsPlusState:
    camera: JPGImage
    your_name: RobotName
    state: DTSimState
    map_data: str


description = """Particularization for Duckiebot1 observations and commands."""
protocol_agent_duckiebot1 = particularize_no_check(
    protocol_agent,
    description=description,
    inputs={"observations": Duckiebot1Observations},
    outputs={"commands": Duckiebot1Commands},
)

description = """Particularization for Duckiebot1; observations and commands with full state """
protocol_agent_duckiebot1_fullstate = particularize_no_check(
    protocol_agent_duckiebot1,
    inputs={"observations": Duckiebot1ObservationsPlusState},
)

protocol_simulator_duckiebot1 = particularize_no_check(
    protocol_simulator,
    description="""Particularization for Duckiebot1 observations and commands.""",
    inputs={
        "set_robot_commands": DB18SetRobotCommands,
        "set_map": DTSetMap,
    },
    outputs={
        "robot_observations": DB18RobotObservations,
        "robot_state": DTSimRobotState,
        "state_dump": DTSimStateDump,
    },
)


### DB20


@dataclass
class DB20Odometry:
    resolution_rad: float
    """ What is the resolution of 1 odometry tick"""
    axis_left_rad: float
    """" The current rotation of the left wheel. Positive when robot goes forward """
    axis_right_rad: float
    """" The current rotation of the right wheel. Positive when robot goes forward """


@dataclass
class DB20OdometryWithTimestamp(DB20Odometry):
    timestamp: float


@dataclass
class DB20Observations:
    camera: JPGImage
    odometry: DB20Odometry


@dataclass
class DB20ObservationsWithTimestamp:
    camera: JPGImageWithTimestamp
    odometry: DB20OdometryWithTimestamp


@dataclass
class DB20ObservationsPlusState:
    camera: JPGImageWithTimestamp
    odometry: DB20OdometryWithTimestamp

    your_name: RobotName
    state: DTSimState
    map_data: str


@dataclass
class DB20ObservationsOnlyState:
    # camera: JPGImage
    # odometry: DB20Odometry

    your_name: RobotName
    state: DTSimState
    map_data: str


@dataclass
class DB20Commands:
    wheels: PWMCommands
    LEDS: LEDSCommands


@dataclass
class DB20SetRobotCommands(SetRobotCommands):
    robot_name: RobotName
    t_effective: float
    commands: DB20Commands


@dataclass
class DB20RobotObservations(RobotObservations):
    robot_name: RobotName
    t_effective: float
    observations: DB20Observations


@dataclass
class DB20RobotObservationsWithTimestamp(RobotObservations):
    robot_name: RobotName
    t_effective: float
    observations: DB20ObservationsWithTimestamp


protocol_agent_DB20 = particularize_no_check(
    protocol_agent,
    description="""Particularization for DB20 observations and commands.""",
    inputs={"observations": DB20Observations},
    outputs={"commands": DB20Commands},
)
protocol_agent_DB20_timestamps = particularize_no_check(
    protocol_agent,
    description="""Particularization for DB20 observations and commands and timestamps.""",
    inputs={"observations": DB20ObservationsWithTimestamp},
    outputs={"commands": DB20Commands},
)

protocol_agent_DB20_fullstate = particularize_no_check(
    protocol_agent_duckiebot1,
    inputs={"observations": DB20ObservationsPlusState},
)

protocol_agent_DB20_onlystate = particularize_no_check(
    protocol_agent_duckiebot1,
    inputs={"observations": DB20ObservationsOnlyState},
)

protocol_simulator_DB20 = particularize_no_check(
    protocol_simulator,
    description="""Particularization for Duckiebot1 observations and commands.""",
    inputs={
        "set_robot_commands": DB20SetRobotCommands,
        "set_map": DTSetMap,
    },
    outputs={
        "robot_observations": DB20RobotObservations,
        "robot_state": DTSimRobotState,
        "duckie_state": DTSimDuckieState,
        "state_dump": DTSimStateDump,
    },
)

protocol_simulator_DB20_timestamps = particularize_no_check(
    protocol_simulator,
    description="""Particularization for Duckiebot1 observations and commands with timestamps""",
    inputs={
        "set_robot_commands": DB20SetRobotCommands,
        "set_map": DTSetMap,
    },
    outputs={
        "robot_observations": DB20RobotObservationsWithTimestamp,
        "robot_state": DTSimRobotState,
        "duckie_state": DTSimDuckieState,
        "state_dump": DTSimStateDump,
    },
)
