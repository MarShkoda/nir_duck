from dataclasses import dataclass

from nose.tools import assert_raises
from zuper_nodes import check_compatible_protocol, IncompatibleProtocol, InteractionProtocol
from zuper_nodes.language import opposite, particularize_no_check

from . import logger


@dataclass
class Empty:
    pass


def test_subprotocol_obs():
    # this is the story of the duckiebot

    protocol_agent = InteractionProtocol(
        description="",
        inputs={"observations": object},
        outputs={"commands": object},
        language="""
           (in:observations ; out:commands)*
            """,
    )

    @dataclass
    class Commands2018:
        u: int

    @dataclass
    class Commands2020:
        u: int
        # v: float

    @dataclass
    class Obs2018:
        camera: float

    @dataclass
    class Obs2020:
        camera: float
        odometry: float

    protocol_agent_2018 = particularize_no_check(
        protocol_agent, inputs={"observations": Obs2018}, outputs={"commands": Commands2018}
    )
    protocol_agent_2020 = particularize_no_check(
        protocol_agent, inputs={"observations": Obs2020}, outputs={"commands": Commands2020}
    )
    # logger.info(protocol_agent_2018=protocol_agent_2018, protocol_agent_2020=protocol_agent_2020)
    # Every agent2018 is an agent2020
    check_compatible_protocol(protocol_agent_2018, protocol_agent_2020)
    assert_raises(IncompatibleProtocol, check_compatible_protocol, protocol_agent_2020, protocol_agent_2018)


def test_subprotocol_cmds():
    # this is the story of the duckiebot
    @dataclass
    class Commands2018:
        u: int

    @dataclass
    class Commands2020:
        u: int
        v: float

    @dataclass
    class Obs2018:
        camera: float

    @dataclass
    class Obs2020:
        camera: float

    protocol_agent = InteractionProtocol(
        description="",
        inputs={"observations": object},
        outputs={"commands": object},
        language="""
           (in:observations ; out:commands)*
            """,
    )

    protocol_agent_2018 = particularize_no_check(
        protocol_agent, inputs={"observations": Obs2018}, outputs={"commands": Commands2018}
    )
    protocol_agent_2020 = particularize_no_check(
        protocol_agent, inputs={"observations": Obs2020}, outputs={"commands": Commands2020}
    )

    # logger.info(protocol_agent_2018=protocol_agent_2018, protocol_agent_2020=protocol_agent_2020)
    # Every agent2020 is an agent2018
    check_compatible_protocol(protocol_agent_2020, protocol_agent_2018)
    assert_raises(IncompatibleProtocol, check_compatible_protocol, protocol_agent_2018, protocol_agent_2020)
    protocol_agent_2020_op = opposite(protocol_agent_2020)
    protocol_agent_2018_op = opposite(protocol_agent_2018)
    check_compatible_protocol(protocol_agent_2018_op, protocol_agent_2020_op)
    assert_raises(
        IncompatibleProtocol, check_compatible_protocol, protocol_agent_2020_op, protocol_agent_2018_op
    )


def test_subprotocol_channels_inputs():

    protocol_agent_2018 = InteractionProtocol(
        description="",
        inputs={"observations": object},
        outputs={"commands": object},
        language="""
           (in:observations ; out:commands)*
            """,
    )

    protocol_agent_2020 = InteractionProtocol(
        description="",
        inputs={"observations": object},
        outputs={"commands": object, "extra": int},
        language="""
           (in:observations ; out:commands)*
            """,
    )

    # Every agent2020 is an agent2018
    check_compatible_protocol(protocol_agent_2020, protocol_agent_2018)
    assert_raises(IncompatibleProtocol, check_compatible_protocol, protocol_agent_2018, protocol_agent_2020)
    protocol_agent_2020_op = opposite(protocol_agent_2020)
    protocol_agent_2018_op = opposite(protocol_agent_2018)
    check_compatible_protocol(protocol_agent_2018_op, protocol_agent_2020_op)
    assert_raises(
        IncompatibleProtocol, check_compatible_protocol, protocol_agent_2020_op, protocol_agent_2018_op
    )


def test_subprotocol_channels_outputs():

    protocol_agent_2018 = InteractionProtocol(
        description="",
        inputs={"observations": object, "extra": int},
        outputs={"commands": object},
        language="""
           (in:observations ; out:commands)*
            """,
    )

    protocol_agent_2020 = InteractionProtocol(
        description="",
        inputs={"observations": object},
        outputs={"commands": object},
        language="""
           (in:observations ; out:commands)*
            """,
    )

    # Every agent2020 is an agent2018
    check_compatible_protocol(protocol_agent_2020, protocol_agent_2018)
    assert_raises(IncompatibleProtocol, check_compatible_protocol, protocol_agent_2018, protocol_agent_2020)
    protocol_agent_2020_op = opposite(protocol_agent_2020)
    protocol_agent_2018_op = opposite(protocol_agent_2018)
    check_compatible_protocol(protocol_agent_2018_op, protocol_agent_2020_op)
    assert_raises(
        IncompatibleProtocol, check_compatible_protocol, protocol_agent_2020_op, protocol_agent_2018_op
    )
