from webamc.db import tables, queries
from webamc.www.all import *


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:
    item_child = queries.get_item(ctx.dbs, args["itr_child"])
    item_parent = queries.get_item(ctx.dbs, args["itr_parent"])
    query = ctx.dbs.query(
        tables.ItemRelation
    ).where(
        tables.ItemRelation.itr_parent == item_parent.itm_id
    ).order_by(
        tables.ItemRelation.itr_order.desc()
    )
    itr = query.first()
    if itr is None:
        order = 1
    else:
        order = itr.itr_order + 1
    itr = tables.ItemRelation(
        itr_parent=item_parent.itm_id,
        itr_child=item_child.itm_id,
        itr_order=order
    )
    ctx.dbs.add(itr)
    return base.wrap_code("succ")
