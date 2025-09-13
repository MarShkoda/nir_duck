# coding=utf-8
import base64
import base58
import six

from .serialization1 import Serializable

__all__ = [
    "GenericData",
]


class GenericData(Serializable):
    prefer_base58 = False

    def __init__(self, bytes_contents, content_type):
        if six.PY3:
            assert isinstance(bytes_contents, bytes), type(bytes_contents)
        self.bytes_contents = bytes_contents
        self.content_type = content_type

    def __repr__(self):
        return "GenericData(%s, len %s)" % (self.content_type, len(self.bytes_contents))

    def params_to_json_dict(self):
        res = {}
        if GenericData.prefer_base58:
            encoded_bytes = base58.b58encode(self.bytes_contents)
            encoded_string = encoded_bytes.decode()
            res["base58"] = encoded_string
        else:
            encoded_bytes = base64.b64encode(self.bytes_contents)
            encoded_string = encoded_bytes.decode()
            res["base64"] = encoded_string
        res["content-type"] = self.content_type
        return res

    @classmethod
    def params_from_json_dict(cls, d):
        if "base64" in d:
            base64s = d.pop("base64")

            bytes_contents = base64.b64decode(base64s)
        else:
            base58s = d.pop("base58")
            bytes_contents = base58.b58decode(base58s)
        content_type = d.pop("content-type")
        return dict(content_type=content_type, bytes_contents=bytes_contents)
