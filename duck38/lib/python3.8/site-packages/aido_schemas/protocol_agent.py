from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from dataclasses import dataclass
else:
    from zuper_typing import dataclass

from .basics import InteractionProtocol

__all__ = ["EpisodeStart", "protocol_agent", "GetCommands"]


@dataclass
class EpisodeStart:
    """Marker for the start of an episode."""

    episode_name: str
    yaml_payload: str = "{}"


@dataclass
class GetCommands:
    at_time: float


protocol_agent = InteractionProtocol(
    description="""

Generic protocol for an agent that receives "observations" and responds 
with "commands".

"episode_start" marks the beginning of an episode.  

    """.strip(),
    inputs={
        "observations": Any,
        "seed": int,
        "get_commands": GetCommands,
        "episode_start": EpisodeStart,
    },
    outputs={"commands": Any},
    language="""
            in:seed? ;
            (   in:episode_start ; 
                (in:observations | 
                    (in:get_commands ; out:commands)
                 )* 
            )*
        """,
)
