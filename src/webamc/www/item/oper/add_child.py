from webamc.db import tables, queries
from webamc.www.all import *
from webamc.www.item import router
from webamc.www.item.page import database_list


def data(
        ctx: context.Context,
        args: router.args_oper_add_child_t
) -> fa.Response:
    item_child = queries.get_item(ctx.dbs, args["itr_child"])
    item_parent = queries.get_item(ctx.dbs, args["itr_parent"])
    result = database_list.div_item(ctx, item_child, item_parent)
    return base.wrap_code("succ", result=str(result))
