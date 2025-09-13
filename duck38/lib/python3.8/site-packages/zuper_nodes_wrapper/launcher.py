import argparse
import os
import sys
import traceback
from dataclasses import dataclass, field
from typing import Dict, Optional

import yaml
from zuper_commons.types import import_name
from zuper_ipce import object_from_ipce
from zuper_typing import debug_print
from . import logger
from zuper_nodes_wrapper.constants import CTRL_ABORTED, CTRL_OVER
from zuper_nodes_wrapper.wrapper import CommContext, open_comms
from .interface import wrap_direct

__all__ = ['launcher_main']


@dataclass
class NodeLaunchConfig:
    node: str
    protocol: str
    config: Dict[str, object] = field(default_factory=dict)

# noinspection PyBroadException
def launcher_main():
    sys.path.append(os.getcwd())
    prog = 'node-launch'
    parser = argparse.ArgumentParser(prog=prog)
    # define arguments
    parser.add_argument(
        "--config", required=True,
        help="Config file (node_launch.yaml)",
    )

    parser.add_argument(
        "--protocol",
        help="Protocol (python symbol)",
    )
    parser.add_argument(
        "--node",
        help="node class (python symbol)",
    )
    parser.add_argument(
        "--check", default=False, action='store_true',
        help="only check symbols importable"
    )

    # parse arguments
    parsed = parser.parse_args()

    errors = []

    node_type = None
    node = None
    config:Optional[NodeLaunchConfig] = None

    def complain(m: str, **kwargs):
        er = m, kwargs
        logger.error(er[0], **er[1])
        errors.append(er)

    if parsed.config:
        if not os.path.exists(parsed.config):
            msg = f'Cannot find path {parsed.config}'
            complain(msg)
        else:
            try:
                with open(parsed.config) as f:
                    data = f.read()
                y = yaml.load(data, Loader=yaml.Loader)
                config = object_from_ipce(y, NodeLaunchConfig)

            except Exception:
                msg = f'Cannot load config file {parsed.config}'
                complain(msg, tb=traceback.format_exc())
    else:
        node_symbol = parsed.node
        protocol_symbol = parsed.protocol
        if node_symbol is None or protocol_symbol is None:
            msg = 'Either specify --config or both --node and --protocol'
            complain(msg)
        else:
            config = NodeLaunchConfig(node=node_symbol, protocol=protocol_symbol, config={})


    protocol = None

    sys.path.append(os.getcwd())
    if not errors:
        try:
            node_type = import_name(config.node)
        except Exception:
            msg = 'Cannot import the node class'
            complain(msg, node_symbol=config.node, tb=traceback.format_exc())

    if parsed.check:
        if errors:
            logger.error('Check not passed')
            sys.exit(1)
        else:
            logger.info('Check passed')
            sys.exit(0)

    if not errors:
        try:
            # noinspection PyCallingNonCallable
            node = node_type()
        except Exception:
            msg = 'Cannot instantiate the node class'
            complain(msg, node_symbol=config.node, node_type=node_type, tb=traceback.format_exc())

    if not errors:
        try:
            protocol = import_name(config.protocol)
        except Exception:
            msg = 'Cannot import the protocol class'
            complain(msg, protocol_symbol=config.protocol, tb=traceback.format_exc())


    if not errors:
        return wrap_direct(node=node, protocol=protocol, args=[])

    else:
        cc: CommContext
        with open_comms('unnamed', logger_meta=logger) as cc:
            msg = debug_print(errors)
            cc.fo_sink.write_control_message(CTRL_ABORTED, msg)
            cc.fo_sink.write_control_message(CTRL_OVER)


if __name__ == '__main__':
    launcher_main()
