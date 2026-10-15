from webamc.db import queries, tables
from webamc.www.all import *
from webamc.www.item import router



def data(
        ctx: context.Context,
        args: router.args_item_t
) -> fa.responses.Response:
    def loop(itm_id: int) -> None:
        children = [c.itm_id for c in queries.get_children(ctx.dbs, itm_id)]
        o = ctx.dbs.query(
            tables.Item
        ).where(
            tables.Item.itm_id == itm_id
        ).first()
        if o is not None:
            ctx.dbs.delete(o)
            for child_itm_id in children:
                if ctx.dbs.query(
                    tables.ItemRelation
                ).where(
                    tables.ItemRelation.itr_child == child_itm_id
                ).first() is None:
                    loop(child_itm_id)

    itm_id = args["itm_id"]
    owner = queries.get_item_owner(ctx.dbs, itm_id)
    if owner is None or owner.usr_id != session.usr_id(ctx):
        raise fa.HTTPException(status_code=403)
    loop(itm_id)
    return base.wrap_code("succ")
