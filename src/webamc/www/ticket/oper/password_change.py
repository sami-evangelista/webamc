#!/usr/bin/env python3

from webamc.www.all import *
from webamc.db import tables, queries, row_op
from webamc.www.ticket import router


def data(
        ctx: context.Context,
        args: router.args_oper_password_change_t
) -> fa.Response:
    if args["loc_password"] != args["loc_password_confirm"]:
        return base.wrap_code("err_invalid_password_confirm")
    tkt_usr = queries.get_ticket(ctx.dbs, args["ticket"])
    if tkt_usr is None:
        return base.wrap_code("err_invalid_ticket")
    tkt, usr = tkt_usr
    if tkt.tkt_type != types.TICKET_PASSWORD_CHANGE:
        return base.wrap_code("err_invalid_ticket")
    values: types.db_map_t = {
        "loc_password": str(args["loc_password"])
    }
    ok, err, values = row_op.check_tbl_values(
        ctx.dbs, "local_auth", values, "update"
    )
    if not ok:
        return fa.responses.JSONResponse({
            "success": False,
            "msgs": list() if err is None else err,
            "result": None
        })
    values = row_op.transform_tbl_values("local_auth", values)
    tkt, usr = tkt_usr
    ctx.dbs.query(
        tables.LocalAuth
    ).where(
        tables.LocalAuth.loc_usr == usr.usr_id
    ).update({
        "loc_password": values["loc_password"]
    })
    ctx.dbs.query(
        tables.Ticket
    ).where(
        tables.Ticket.tkt_id == tkt.tkt_id
    ).delete()
    return base.wrap_code("succ_password_changed")
