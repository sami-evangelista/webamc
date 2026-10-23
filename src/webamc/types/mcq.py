import typing as tp
import typing_extensions as tp_ext

from . import item


mcq_content_t = tp_ext.TypedDict(
    "mcq_content_t",
    {
        "itm_id": int,
        "itm_type": item.item_type_t,
        "iti_num": int,
        "children": None | list["mcq_content_t"]
    }
)


def mcq_enum_items(
        content: mcq_content_t,
        parent: mcq_content_t | None = None
) -> tp.Generator[tuple[mcq_content_t, None | mcq_content_t]]:
    yield content, parent
    if content["children"] is not None:
        for c in content["children"]:
            yield from mcq_enum_items(c, content)
