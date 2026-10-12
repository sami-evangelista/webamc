from webamc.www.all import *
from webamc.actions import compile as comp
from webamc.db import tables
from webamc.www.item import router


def data(
        ctx: context.Context,
        args: router.args_oper_save_pack_t
) -> fa.Response:

    # insert into item
    item = tables.Item(
        itm_code=args["code"],
        itm_title=args["title"],
        itm_standalone=True,
        itm_type=types.ITEM_TYPE_PACK,
        itm_rnd=False,
        itm_difficulty=None,
        itm_usr=session.usr_id(ctx),
        itm_visible=True
    )
    ctx.dbs.add(item)
    ctx.dbs.flush()
    ctx.dbs.refresh(item)

    # insert into mcq
    mcq = tables.Mcq(
        mcq_id=item.itm_id
    )
    ctx.dbs.add(mcq)

    # insert into pack
    spec = comp.check_pack(args["pack"])
    pack = tables.Pack(
        pak_id=item.itm_id,
        pak_spec=spec
    )
    ctx.dbs.add(pack)

    response = {
        "success": True,
        "msgs": list(),
        "result": None
    }
    return fa.responses.JSONResponse(response)
