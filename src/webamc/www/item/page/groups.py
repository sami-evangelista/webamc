from webamc.www.all import *


def page(ctx: context.Context, itm_id: None | int) -> he.Element:
    from . import group
    return group.page(ctx, None)
