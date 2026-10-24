from webamc.www.all import *
from webamc.db import tables, queries


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:

    if args["loc_password"] != args["loc_password_confirm"]:
        return base.wrap_code("err_invalid_password_confirm")
    tkt_usr = queries.get_ticket(ctx.dbs, args["ticket"])
    if tkt_usr is None:
        return base.wrap_code("err_invalid_ticket")
    tkt, usr = tkt_usr
    if tkt.tkt_type != types.TICKET_PASSWORD_CHANGE:
        return base.wrap_code("err_invalid_ticket")
    tkt, usr = tkt_usr

    # update password
    select = sa.select(
        tables.LocalAuth
    ).where(
        tables.LocalAuth.loc_usr == usr.usr_id
    )
    loc = ctx.dbs.scalars(select).first()
    assert loc is not None
    loc.loc_password = args["loc_password"]

    # delete ticket
    ctx.dbs.query(
        tables.Ticket
    ).where(
        tables.Ticket.tkt_id == tkt.tkt_id
    ).delete()
    return base.wrap_code("succ_password_changed")
