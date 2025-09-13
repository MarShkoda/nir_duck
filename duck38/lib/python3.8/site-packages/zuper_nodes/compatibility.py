from zuper_commons.types import ZException
from zuper_typing import can_be_used_as2

from .language import InteractionProtocol

__all__ = ["IncompatibleProtocol", "check_compatible_protocol"]


class IncompatibleProtocol(ZException):
    pass


def check_compatible_protocol(p1: InteractionProtocol, p2: InteractionProtocol):
    """
        Checks that p1 is a subprotocol of p2, that is, we can use a p1-node
        wherever a p2-node fits.

        :raises: IncompatibleProtocol
    """
    try:
        # check input compatibility

        # p1 should not need more input
        p1_needs_more = set(p1.inputs) - set(p2.inputs)
        if p1_needs_more:
            msg = f"P1 needs more inputs."
            raise IncompatibleProtocol(
                msg, p1_inputs=sorted(p1.inputs), p2_inputs=sorted(p2.inputs), p1_needs_more=p1_needs_more
            )

        # p1 should have all the outputs
        p1_missing_output = set(p2.outputs) - set(p1.outputs)
        if p1_missing_output:
            msg = f"P1 has missing outputs."
            raise IncompatibleProtocol(
                msg,
                p1_outputs=sorted(p1.outputs),
                p2_outputs=sorted(p2.outputs),
                p1_missing_output=p1_missing_output,
            )
        common_inputs = set(p1.inputs) & set(p2.inputs)
        for k in common_inputs:
            v1 = p1.inputs[k]
            v2 = p2.inputs[k]

            r = can_be_used_as2(v2, v1)
            if not r:
                msg = f'For input "{k}", cannot use type v2 as v1'
                raise IncompatibleProtocol(
                    msg, k=k, v1=v1, v2=v2, r=r, p1_inputs=p1.inputs, p2_inputs=p2.inputs
                )

        # check output compatibility
        common_ouputs = set(p1.outputs) & set(p2.outputs)
        for k in common_ouputs:
            v1 = p1.outputs[k]
            v2 = p2.outputs[k]
            r = can_be_used_as2(v1, v2)
            if not r:
                msg = f'For output "{k}", cannot use type v1 as v2.'
                raise IncompatibleProtocol(
                    msg, k=k, v1=v1, v2=v2, r=r, p1_outputs=p1.outputs, p2_outputs=p2.outputs
                )
            # XXX: to finish
    except IncompatibleProtocol as e:
        msg = "Cannot say that p1 is a sub-protocol of p2"
        raise IncompatibleProtocol(msg, p1=p1, p2=p2) from e
