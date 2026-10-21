from webamc.db import tables, queries
from webamc.www.all import *


def data(
        ctx: context.Context,
        args: types.args_route_item_oper_add_child_t
) -> fa.Response:
    item_child = queries.get_item(ctx.dbs, args["itr_child"])
    item_parent = queries.get_item(ctx.dbs, args["itr_parent"])
    query = ctx.dbs.query(
        tables.ItemRelation.itr_order
    ).where(
        tables.ItemRelation.itr_parent == item_parent.itm_id
    ).order_by(
        tables.ItemRelation.itr_order.desc()
    )
    order = ctx.dbs.scalars(query).first()
    if order is None:
        order = 1
    else:
        order = order + 1
    itr = tables.ItemRelation(
        itr_parent=item_parent.itm_id,
        itr_child=item_child.itm_id,
        itr_order=order
    )
    ctx.dbs.add(itr)
    return base.wrap_code("succ")
