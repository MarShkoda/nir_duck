from zuper_commons.types import ZValueError


class ZDeserializationError(ZValueError):
    pass


class ZDeserializationErrorSchema(ZDeserializationError):
    pass


# class ZSerializationError(ZValueError):
#     pass


#
# class ZInvalidSchema(ZValueError):
#     pass
