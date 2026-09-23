import typing as tp
import json
import typeguard

from . import item


def check_pack_spec(spec: str) -> item.pack_spec_t:
    try:
        return tp.cast(
            item.pack_spec_t,
            typeguard.check_type(json.loads(spec), item.pack_spec_t)
        )
    except (typeguard.TypeCheckError, json.decoder.JSONDecodeError) as ex:
        raise ValueError from ex
