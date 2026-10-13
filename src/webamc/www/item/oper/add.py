from webamc.www.all import *
from webamc.www.item import router
from webamc.db import tables, errors as db_errors


def data(ctx: context.Context, args: router.args_oper_add_t) -> fa.Response:
    itm_type = args["itm_type"]
    itm_is_mcq = args["type"] == "mcq"
    itm_code = args["itm_code"]
    itm_title = args["itm_title"]

    # insert into item
    item = tables.Item(
        itm_code=itm_code,
        itm_title=itm_title,
        itm_standalone=True,
        itm_type=itm_type,
        itm_rnd=False,
        itm_difficulty=None,
        itm_usr=session.usr_id(ctx),
        itm_visible=True,
        itm_is_mcq=itm_is_mcq
    )
    ctx.dbs.add(item)
    ctx.dbs.flush()
    ctx.dbs.refresh(item)

    # insert into pack or exercise
    if itm_type == types.ITEM_TYPE_PACK:
        pak_spec: types.pack_spec_t = {"op": "all"}
        pack = tables.Pack(
            pak_id=item.itm_id,
            pak_spec=json.dumps(pak_spec)
        )
        ctx.dbs.add(pack)
    elif itm_type == types.ITEM_TYPE_EXERCISE:
        exe = tables.Exercise(
            exe_id=item.itm_id
        )
        ctx.dbs.add(exe)
    else:
        assert False

    # insert into instance
    inst = tables.ItemInstance(
        iti_num=1,
        iti_item=item.itm_id,
        iti_seed=0
    )
    ctx.dbs.add(inst)

    # insert into mcq
    if itm_is_mcq:
        mcq = tables.Mcq(
            mcq_id=item.itm_id
        )
        ctx.dbs.add(mcq)

    return base.wrap_code("succ", result={"itm_id": item.itm_id})
