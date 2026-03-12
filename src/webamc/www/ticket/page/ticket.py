#!/usr/bin/env python3

from webamc.www.all import *
from webamc.db import queries, desc, tables, row_op
from webamc.www.db import util as www_db_util


def page(
        ctx: context.Context,
        ticket: str
) -> fa.Response:
    tkt = ctx.dbs.query(
        tables.Ticket
    ).where(
        tables.Ticket.tkt_value==ticket
    ).first()
    if tkt is None:
        return base.page(
            ctx,
            str(he.Txt("page_title_ticket_error")),
            he.Txt("err_invalid_ticket")
        )
    if tkt.tkt_type == types.TICKET_ACCOUNT_CREATION:
        return _page_account_creation(ctx, tkt)
    elif tkt.tkt_type == types.TICKET_PASSWORD_CHANGE:
        return _page_password_change(ctx, tkt)
    elif tkt.tkt_type == types.TICKET_EADDR_CHANGE:
        return _page_eaddr_change(ctx, tkt)
    raise fa.HTTPException(status_code=500)


def _page_password_change(
        ctx: context.Context,
        tkt: tables.Ticket
) -> fa.Response:
    assert tkt.tkt_usr is not None
    usr = queries.get_usr(ctx.dbs, tkt.tkt_usr)
    assert usr is not None
    input_confirm = he.Input(type_="password", id_="loc_password_confirm")
    desc_usr_code = desc.col_desc("usr_code")
    trs = [
        he.Tr(he.Td(he.Txt(desc_usr_code)), he.Td(he.Str(usr.usr_code)))
    ] + [
        he.Tr(he.Td(txt), he.Td(element))
        for txt, element in www_db_util.get_txt_and_input(
                ctx, ["loc_password"]
        )
    ] + [
        he.Tr(he.Td(he.Txt("name_confirmation")), he.Td(input_confirm))
    ]
    table = he.Table(*trs, id_="table-password-change", class_="table-form")
    img = base.static_img(
        "checkmark",
        "verb_send",
        js=f"ticket_password_change('{tkt.tkt_value}')",
        class_="submit"
    )
    div = he.Div(
        table,
        img,
        class_="box"
    )
    return base.page(
        ctx,
        str(he.Txt("page_title_password_change")),
        div
    )


def _page_eaddr_change(
        ctx: context.Context,
        tkt: tables.Ticket
) -> fa.Response:
    assert tkt.tkt_usr is not None
    usr = queries.get_usr(ctx.dbs, tkt.tkt_usr)
    assert usr is not None
    values: types.db_map_t = {
        "usr_eaddr": tkt.tkt_eaddr
    }
    ok, err, values = row_op.check_tbl_values(ctx.dbs, "usr", values, "update")
    if not ok:
        if err is None or err == list():
            msg: he.Element = he.Empty()
        else:
            msg = he.Str(err[0])
    else:
        ctx.dbs.query(
            tables.Usr
        ).where(
            tables.Usr.usr_id == usr.usr_id
        ).update({
            "usr_eaddr": values["usr_eaddr"]
        })
        ctx.dbs.query(
            tables.Ticket
        ).where(
            tables.Ticket.tkt_id == tkt.tkt_id
        ).delete()
        msg = he.Txt("succ_eaddr_changed")
    return base.page(
        ctx,
        str(he.Txt("page_title_eaddr_change")),
        msg
    )


def _page_account_creation(
        ctx: context.Context,
        tkt: tables.Ticket
) -> fa.Response:
    input_confirm = he.Input(type_="password", id_="loc_password_confirm")
    fields = ["usr_code", "usr_fst_name", "usr_name", "loc_password"]
    desc_usr_eaddr = desc.col_desc("usr_eaddr")
    trs = [
        he.Tr(he.Td(he.Txt(desc_usr_eaddr)), he.Td(he.Str(tkt.tkt_eaddr)))
    ] + [
        he.Tr(he.Td(txt), he.Td(element))
        for txt, element in www_db_util.get_txt_and_input(
                ctx, fields
        )
    ] + [
        he.Tr(he.Td(he.Txt("name_confirmation")), he.Td(input_confirm))
    ]
    table = he.Table(*trs, class_="table-form")
    a_send = base.static_img(
        "checkmark",
        "verb_send",
        js=f"ticket_account_creation('{tkt.tkt_value}')",
        class_="submit"
    )
    input_eaddr = he.Input(
        id_="usr_eaddr",
        value=tkt.tkt_eaddr,
        type_="hidden"
    )
    div = he.Div(
        table,
        a_send,
        input_eaddr,
        id_="table-account-creation",
        class_="box"
    )
    return base.page(
        ctx,
        str(he.Txt("page_title_account_creation")),
        div
    )
