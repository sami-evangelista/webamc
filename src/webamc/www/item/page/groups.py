from webamc.www.all import *
from webamc.www.item import router


def page(
        ctx: context.Context,
        item_id: int
) -> he.Element:
    from . import group
    return group.page(ctx, None)
