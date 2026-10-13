from webamc.www.all import *
from webamc.db import tables, errors as db_errors
from webamc.www.ticket import router


def data(
        ctx: context.Context,
        args: router.args_oper_account_creation_t
) -> fa.Response:
    if not config.CONFIG["auth_account_creation_enabled"]:
        raise fa.HTTPException(status_code=403)

    usr_values: types.db_map_t = {
        "usr_code": args["usr_code"],
        "usr_eaddr": args["usr_eaddr"],
        "usr_fst_name": args["usr_fst_name"],
        "usr_name": args["usr_name"]
    }
    loc_values: types.db_map_t = {
        "loc_enabled": True,
        "loc_password": args["loc_password"],
        "loc_login": args["usr_code"]
    }
    
    # insert usr
    usr = tables.Usr(
        usr_code=str(usr_values["usr_code"]),
        usr_eaddr=str(usr_values["usr_eaddr"]),
        usr_fst_name=str(usr_values["usr_fst_name"]),
        usr_name=str(usr_values["usr_name"])
    )
    ctx.dbs.add(usr)
    ctx.dbs.flush()
    ctx.dbs.refresh(usr)

    # insert local_auth
    loc = tables.LocalAuth(
        loc_enabled=bool(loc_values["loc_enabled"]),
        loc_password=str(loc_values["loc_password"]),
        loc_login=str(loc_values["loc_login"]),
        loc_usr=usr.usr_id
    )
    ctx.dbs.add(loc)

    return base.wrap_code("succ_account_created")
