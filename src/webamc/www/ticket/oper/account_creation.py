from webamc.www.all import *
from webamc.db import tables
from webamc.www.ticket import router


def data(
        ctx: context.Context,
        args: router.args_oper_account_creation_t
) -> fa.Response:
    if not config.CONFIG["auth_account_creation_enabled"]:
        raise fa.HTTPException(status_code=403)

    # insert usr
    usr = tables.Usr(
        usr_code=str(args["usr_code"]),
        usr_eaddr=str(args["usr_eaddr"]),
        usr_fst_name=str(args["usr_fst_name"]),
        usr_name=str(args["usr_name"])
    )
    ctx.dbs.add(usr)
    ctx.dbs.flush()
    ctx.dbs.refresh(usr)

    # insert local_auth
    loc = tables.LocalAuth(
        loc_enabled=bool(True),
        loc_password=str(args["loc_password"]),
        loc_login=str(args["usr_code"]),
        loc_usr=usr.usr_id
    )
    ctx.dbs.add(loc)

    return base.wrap_code("succ_account_created")
