from zuper_nodes_wrapper import Context
from zuper_nodes_wrapper.constants import ENV_AIDO_REQUIRE_GPU
import os

__all__ = ["no_hardware_GPU_available"]


def should_bail_if_no_hardware_GPU(context: Context) -> bool:
    req = os.environ.get(ENV_AIDO_REQUIRE_GPU, None)
    if req is None:
        return False
    else:
        msg = f"{ENV_AIDO_REQUIRE_GPU}: {req!r}"
        context.error(msg)
        return True


def no_hardware_GPU_available(context: Context):
    if should_bail_if_no_hardware_GPU(context):
        msg = "I need a GPU; bailing."
        context.error(msg)
        raise SystemExit(138)
        # raise Exception(msg)
