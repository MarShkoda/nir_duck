from .basics import InteractionProtocol
from .protocol_agent import EpisodeStart
from .protocol_simulator import JPGImage

__all__ = ["protocol_image_filter", "protocol_image_source"]

protocol_image_filter = InteractionProtocol(
    description="""An image filter. Takes an image, returns an image.""",
    inputs={"image": JPGImage, "episode_start": EpisodeStart},
    outputs={"image": JPGImage, "episode_start": EpisodeStart},
    language="""
        (in:episode_start ; out:episode_start ; (in:image ; out:image)*)*
        """,
)

protocol_image_source = InteractionProtocol(
    description="""

An abstraction over logs of images. 

It emits a series of EpisodeStart followed by a set of images.

    """,
    inputs={"next_image": type(None), "next_episode": type(None)},
    outputs={
        "image": JPGImage,
        "episode_start": EpisodeStart,
        "no_more_images": type(None),
        "no_more_episodes": type(None),
    },
    language="""
                (
                    in:next_episode ; (
                        out:no_more_episodes | 
                        (out:episode_start ;
                            (in:next_image ; (out:image | out:no_more_images))*)
                    )
                )*            
            """,
)
