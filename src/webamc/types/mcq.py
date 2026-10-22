import typing as tp
import typing_extensions as tp_ext


mcq_content_t = tp_ext.TypedDict(
    "mcq_content_t",
    {
        "itm_id": int,
        "iti_num": int,
        "children": None | list["mcq_content_t"]
    }
)


def mcq_enum_items(
        content: mcq_content_t,
        parent: int | None
) -> tp.Generator[tuple[int, int, int | None]]:
    yield (content["itm_id"], content["iti_num"], parent)
    if content["children"] is not None:
        for c in content["children"]:
            yield from mcq_enum_items(c, content["itm_id"])
