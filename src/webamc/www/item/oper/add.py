from webamc.www.all import *
from webamc.db import tables


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:
    itm_type = args["itm_type"]
    itm_is_mcq = args["itm_exe_or_mcq"] == "mcq"
    itm_code = args["itm_code"]
    itm_title = args["itm_title"]
    if itm_type != types.ITEM_TYPE_PACK:
        itm_pack_spec = None
    else:
        itm_pack_spec = json.dumps({"op": "all"})

    # insert into item
    item = tables.Item(
        itm_code=itm_code,
        itm_title=itm_title,
        itm_type=itm_type,
        itm_rnd=False,
        itm_difficulty=None,
        itm_usr=session.usr_id(ctx),
        itm_visible=True,
        itm_is_mcq=itm_is_mcq,
        itm_pack_spec=itm_pack_spec
    )
    ctx.dbs.add(item)
    ctx.dbs.flush()
    ctx.dbs.refresh(item)

    # insert into instance
    inst = tables.ItemInstance(
        iti_num=1,
        iti_item=item.itm_id,
        iti_seed=0
    )
    ctx.dbs.add(inst)

    return base.wrap_code("succ", result={"itm_id": item.itm_id})
