from webamc.db import queries, tables
from webamc.www.all import *


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:
    def loop(itm_id: int) -> None:
        children = [c.itm_id for c in queries.get_children(ctx.dbs, itm_id)]
        item = queries.get_item(ctx.dbs, itm_id)
        ctx.dbs.delete(item)
        for child_itm_id in children:
            is_orphan = ctx.dbs.query(
                tables.ItemRelation
            ).where(
                tables.ItemRelation.itr_child == child_itm_id
            ).first() is None
            if is_orphan:
                loop(child_itm_id)

    itm_id = args["itm_id"]
    owner = queries.get_item_owner(ctx.dbs, itm_id)
    if owner is None or owner.usr_id != session.usr_id(ctx):
        raise fa.HTTPException(status_code=403)
    loop(itm_id)
    return base.wrap_code("succ")
