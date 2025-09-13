from __future__ import unicode_literals
import json
import sys

from duckietown_serialization_ds1 import Serializable


def cli_parse_json():
    i = sys.stdin

    for line in i.readlines():
        j = json.loads(line)
        ob = Serializable.from_json_dict(j)
        # print(ob)
        d = ob.as_json_dict()
        j2 = json.dumps(d)
        print(j2)


if __name__ == "__main__":
    cli_parse_json()
