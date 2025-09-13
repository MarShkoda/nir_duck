from .basics import InteractionProtocol

__all__ = ["protocol_simple_predictor"]

protocol_simple_predictor = InteractionProtocol(
    description="""

An estimator receives a stream of values and must predict the next value.

    """.strip(),
    inputs={"observations": float, "seed": int, "get_prediction": type(None)},
    outputs={"prediction": float},
    language="""
            in:seed? ;
        
            (in:observations | 
                (in:get_prediction ; out:prediction)
             )*
        """,
)
