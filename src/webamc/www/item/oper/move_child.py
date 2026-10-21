from webamc.db import tables
from webamc.www.all import *


def data(
        ctx: context.Context,
        args: types.args_route_item_oper_move_child_t
) -> fa.Response:
    query = ctx.dbs.query(
        tables.ItemRelation
    ).where(
        tables.ItemRelation.itr_parent == args["itr_parent"]
    ).order_by(
        tables.ItemRelation.itr_order
    )
    relation = list(ctx.dbs.scalars(query))
    gen = (
        i for i, tr in enumerate(relation)
        if tr.itr_child == args["itr_child"]
    )
    idx = next(gen, None)
    assert idx is not None
    idx_other = idx + args["move"]

    # swap orders of the two items
    if 0 <= idx_other < len(relation):
        itr_order_item = relation[idx].itr_order
        itr_order_other = relation[idx_other].itr_order
        relation[idx].itr_order = relation[-1].itr_order + 1
        relation[idx_other].itr_order = relation[-1].itr_order + 2
        ctx.dbs.commit()
        relation[idx_other].itr_order = itr_order_item
        relation[idx].itr_order = itr_order_other
        ctx.dbs.commit()

    return base.wrap_code("succ")
