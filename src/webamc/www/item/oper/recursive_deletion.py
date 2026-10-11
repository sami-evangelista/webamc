from webamc.db import queries, tables
from webamc.www.all import *
from webamc.www.item import router



def data(
        ctx: context.Context,
        args: router.args_item_t
) -> fa.responses.Response:
    def loop(itm_id: int) -> None:
        children = [c.itm_id for c in queries.get_children(ctx.dbs, itm_id)]
        ctx.dbs.query(
            tables.Item
        ).where(
            tables.Item.itm_id == itm_id
        ).delete()
        for child_itm_id in children:
            no_parent_anymore = ctx.dbs.query(
                tables.ItemRelation
            ).where(
                tables.ItemRelation.itr_child == child_itm_id
            ).first() is None
            if no_parent_anymore:
                loop(child_itm_id)

    itm_id = args["itm_id"]
    owner = queries.get_item_owner(ctx.dbs, itm_id)
    if owner is None or owner.usr_id != session.usr_id(ctx):
        raise fa.HTTPException(status_code=403)
    loop(itm_id)
    response = {
        "success": True,
        "msgs": list(),
        "result": None
    }
    return fa.responses.JSONResponse(response)
