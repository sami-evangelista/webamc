#!/usr/bin/env python3

from webamc.www.all import *
from webamc.www.item import router


def page(
        ctx: context.Context,
        **kwargs: tp.Unpack[router.args_page_item_t]
) -> he.Element:
    from . import group
    return group.page(ctx, None)
