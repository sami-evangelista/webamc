#!/usr/bin/env python3

from webamc.www.all import *
from webamc.db import tables, row_op
from webamc.www.ticket import router


def data(
        ctx: context.Context,
        args: router.args_oper_account_creation_t
) -> fa.Response:
    def error(err: None | list[str]) -> fa.Response:
        msgs = list() if err is None else err
        resp = {"success": False, "msgs": msgs, "result": None}
        return fa.responses.JSONResponse(resp)
    if not config.CONFIG["auth_account_creation_enabled"]:
        raise fa.HTTPException(status_code=403)

    usr_values: types.db_map_t = {
        "usr_code": args["usr_code"],
        "usr_eaddr": args["usr_eaddr"],
        "usr_fst_name": args["usr_fst_name"],
        "usr_name": args["usr_name"]
    }
    ok, err, usr_values = row_op.check_tbl_values(
        ctx.dbs, "usr", usr_values, "insert"
    )
    usr_values = row_op.transform_tbl_values("usr", usr_values)
    if not ok:
        return error(err)

    loc_values: types.db_map_t = {
        "loc_enabled": True,
        "loc_password": args["loc_password"],
        "loc_login": args["usr_code"]
    }
    ok, err, loc_values = row_op.check_tbl_values(
        ctx.dbs, "local_auth", loc_values, "insert"
    )
    if not ok:
        return error(err)
    loc_values = row_op.transform_tbl_values("local_auth", loc_values)

    usr = tables.Usr(
        usr_code=str(usr_values["usr_code"]),
        usr_eaddr=str(usr_values["usr_eaddr"]),
        usr_fst_name=str(usr_values["usr_fst_name"]),
        usr_name=str(usr_values["usr_name"])
    )
    ctx.dbs.add(usr)
    ctx.dbs.flush()
    ctx.dbs.refresh(usr)
    loc = tables.LocalAuth(
        loc_enabled=bool(loc_values["loc_enabled"]),
        loc_password=str(loc_values["loc_password"]),
        loc_login=str(loc_values["loc_login"]),
        loc_usr=usr.usr_id
    )
    ctx.dbs.add(loc)
    return base.wrap_code("succ_account_created")
