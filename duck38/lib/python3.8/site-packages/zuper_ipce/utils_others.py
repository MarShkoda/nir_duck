import hashlib
import json
import os
from typing import Optional

import cbor2
import multihash
import numpy as np
from cid import make_cid
from nose.tools import assert_equal

from zuper_commons.fs import write_bytes_to_file, write_ustring_to_utf8_file
from zuper_commons.text import pretty_dict
from zuper_commons.types import ZAssertionError, ZValueError
from zuper_typing import assert_equivalent_types, debug_print, get_patches
from . import logger
from .constants import IEDO, IEDS, IESO
from .conv_ipce_from_object import ipce_from_object
from .conv_ipce_from_typelike import ipce_from_typelike
from .conv_object_from_ipce import object_from_ipce, object_from_ipce_
from .conv_typelike_from_ipce import typelike_from_ipce
from .json_utils import (
    decode_bytes_before_json_deserialization,
    encode_bytes_before_json_serialization,
)

# from .pretty import pretty_dict
from .utils_text import oyaml_dump


def get_cbor_dag_hash_bytes__(ob_cbor: bytes) -> str:
    if not isinstance(ob_cbor, bytes):
        msg = "Expected bytes."
        raise ZValueError(msg, ob_cbor=ob_cbor)
    ob_cbor_hash = hashlib.sha256(ob_cbor).digest()
    mh = multihash.encode(digest=ob_cbor_hash, code=18)
    # the above returns a bytearray
    mh = bytes(mh)
    cid = make_cid(1, "dag-cbor", mh)
    res = cid.encode().decode("ascii")
    return res


def save_object(x: object, ipce: object):
    # noinspection PyBroadException
    # try:
    #     import zuper_ipcl
    # except:
    #     return
    # print(f"saving {x}")
    _x2 = object_from_ipce(ipce)
    ipce_bytes = cbor2.dumps(ipce, canonical=True, value_sharing=True)

    # from zuper_ipcl.debug_print_ import debug_print

    digest = get_cbor_dag_hash_bytes__(ipce_bytes)
    dn = "test_objects"
    # if not os.path.exists(dn):
    #     os.makedirs(dn)
    fn = os.path.join(dn, digest + ".ipce.cbor.gz")
    if os.path.exists(fn):
        pass
    else:  # pragma: no cover
        fn = os.path.join(dn, digest + ".ipce.cbor")
        write_bytes_to_file(ipce_bytes, fn)
        # fn = os.path.join(dn, digest + '.ipce.yaml')
        # write_ustring_to_utf8_file(yaml.dump(y1), fn)
        fn = os.path.join(dn, digest + ".object.ansi")
        s = debug_print(x)  # '\n\n as ipce: \n\n' + debug_print(ipce) \
        write_ustring_to_utf8_file(s, fn)
        fn = os.path.join(dn, digest + ".ipce.yaml")
        s = oyaml_dump(ipce)
        write_ustring_to_utf8_file(s, fn)


def assert_type_roundtrip(T, *, use_globals: Optional[dict] = None, expect_type_equal: bool = True):
    assert_equivalent_types(T, T)
    if use_globals is None:
        use_globals = {}

    schema0 = ipce_from_typelike(T, globals0=use_globals)

    # why 2?
    schema = ipce_from_typelike(T, globals0=use_globals)
    save_object(T, ipce=schema)

    # logger.info(debug_print('schema', schema=schema))
    iedo = IEDO(use_remembered_classes=False, remember_deserialized_classes=False)
    T2 = typelike_from_ipce(schema, iedo=iedo)

    # TODO: in 3.6 does not hold for Dict, Union, etc.
    # if hasattr(T, '__qualname__'):
    #     assert hasattr(T, '__qualname__')
    #     assert T2.__qualname__ == T.__qualname__, (T2.__qualname__, T.__qualname__)

    # if False:
    #     rl.pp('\n\nschema', schema=json.dumps(schema, indent=2))
    #     rl.pp(f"\n\nT ({T})  the original one", **getattr(T, '__dict__', {}))
    #     rl.pp(f"\n\nT2 ({T2}) - reconstructed from schema ", **getattr(T2, '__dict__', {}))

    # pprint("schema", schema=json.dumps(schema, indent=2))

    try:
        assert_equal(schema, schema0)
        if expect_type_equal:
            # assert_same_types(T, T)
            # assert_same_types(T2, T)
            assert_equivalent_types(T, T2, assume_yes=set())
    except:  # pragma: no cover
        logger.info("assert_type_roundtrip", T=T, schema=schema, T2=T2)
        raise
    schema2 = ipce_from_typelike(T2, globals0=use_globals)
    if schema != schema2:  # pragma: no cover
        msg = "Different schemas"
        d = {
            "T": T,
            "T.qual": T.__qualname__,
            "TAnn": T.__annotations__,
            "Td": T.__dict__,
            "schema": schema0,
            "T2": T2,
            "T2.qual": T2.__qualname__,
            "TAnn2": T2.__annotations__,
            "Td2": T2.__dict__,
            "schema2": schema2,
            "patches": get_patches(schema, schema2),
        }
        # msg = pretty_dict(msg, d)
        # print(msg)
        # with open("tmp1.json", "w") as f:
        #     f.write(json.dumps(schema, indent=2))
        # with open("tmp2.json", "w") as f:
        #     f.write(json.dumps(schema2, indent=2))

        # assert_equal(schema, schema2)
        raise ZAssertionError(msg, **d)
    return T2


def assert_object_roundtrip(
    x1, *, use_globals: Optional[dict] = None, expect_equality=True, works_without_schema=True,
):
    """

        expect_equality: if __eq__ is preserved

        Will not be preserved if use_globals = {}
        because a new Dataclass will be created
        and different Dataclasses with the same fields do not compare equal.

    """
    if use_globals is None:
        use_globals = {}
    ieds = IEDS(use_globals, {})
    iedo = IEDO(use_remembered_classes=False, remember_deserialized_classes=False)

    # dumps = lambda x: yaml.dump(x)

    y1 = ipce_from_object(x1, globals_=use_globals)
    y1_cbor: bytes = cbor2.dumps(y1)

    save_object(x1, ipce=y1)

    y1 = cbor2.loads(y1_cbor)

    y1e = encode_bytes_before_json_serialization(y1)
    y1es = json.dumps(y1e, indent=2)

    y1esl = decode_bytes_before_json_deserialization(json.loads(y1es))

    y1eslo = object_from_ipce_(y1esl, object, ieds=ieds, iedo=iedo)

    x1b = object_from_ipce_(y1, object, ieds=ieds, iedo=iedo)

    x1bj = ipce_from_object(x1b, globals_=use_globals)

    check_equality(x1, x1b, expect_equality)

    patches = get_patches(y1, x1bj)
    if not patches and y1 != x1bj:
        pass  # something weird
    if patches:  # pragma: no cover
        # patches = get_patches(y1, x1bj)
        # if patches:
        #     msg = "The objects are not equivalent"
        #     raise ZValueError(msg, y1=y1, x1bj=x1bj, patches=patches)
        msg = "Round trip not obtained"
        # if not patches:
        #     msg += "  but no patches??? "
        # msg = pretty_dict(
        #     "Round trip not obtained",
        #     # dict(x1bj_json=oyaml_dump(x1bj), y1_json=oyaml_dump(y1)),
        # )
        # assert_equal(y1, x1bj, msg=msg)
        if "propertyNames" in y1["$schema"]:
            assert_equal(
                y1["$schema"]["propertyNames"], x1bj["$schema"]["propertyNames"], msg=msg,
            )
        #
        # with open("y1.json", "w") as f:
        #     f.write(oyaml_dump(y1))
        # with open("x1bj.json", "w") as f:
        #     f.write(oyaml_dump(x1bj))

        raise ZAssertionError(msg, y1=y1, x1bj=x1bj, patches=patches)

    # once again, without schema
    ieso_false = IESO(with_schema=False)
    if works_without_schema:
        z1 = ipce_from_object(x1, globals_=use_globals, ieso=ieso_false)
        z2 = cbor2.loads(cbor2.dumps(z1))
        u1 = object_from_ipce_(z2, type(x1), ieds=ieds, iedo=iedo)
        check_equality(x1, u1, expect_equality)

    return locals()


def check_equality(x1: object, x1b: object, expect_equality: bool) -> None:
    if isinstance(x1b, type) and isinstance(x1, type):
        # logger.warning("Skipping type equality check for %s and %s" % (x1b, x1))
        pass
    else:
        if isinstance(x1, np.ndarray):  # pragma: no cover
            pass
        else:

            eq1 = x1b == x1
            eq2 = x1 == x1b

            if expect_equality:  # pragma: no cover

                if not eq1:
                    m = "Object equality (next == orig) not preserved"
                    msg = pretty_dict(
                        m, dict(x1b=x1b, x1b_=type(x1b), x1=x1, x1_=type(x1), x1b_eq=x1b.__eq__,),
                    )
                    raise AssertionError(msg)
                if not eq2:
                    m = "Object equality (orig == next) not preserved"
                    msg = pretty_dict(
                        m, dict(x1b=x1b, x1b_=type(x1b), x1=x1, x1_=type(x1), x1_eq=x1.__eq__,),
                    )
                    raise AssertionError(msg)
            else:
                if eq1 and eq2:  # pragma: no cover
                    msg = "You did not expect equality but they actually are"
                    logger.info(msg)
                    # raise Exception(msg)
