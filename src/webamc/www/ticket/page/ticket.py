from webamc.www.all import *
from webamc.db import queries, desc, tables, errors as db_errors
from webamc.www.db.util import get_txt_and_input


def page(
        ctx: context.Context,
        ticket: str
) -> fa.Response:
    tkt = ctx.dbs.query(
        tables.Ticket
    ).where(
        tables.Ticket.tkt_value == ticket
    ).first()
    if tkt is None:
        body = he.Txt("err_invalid_ticket")
        return base.page(ctx, "page_title_ticket_error", body)
    if tkt.tkt_type == types.TICKET_ACCOUNT_CREATION:
        return _page_account_creation(ctx, tkt)
    if tkt.tkt_type == types.TICKET_PASSWORD_CHANGE:
        return _page_password_change(ctx, tkt)
    if tkt.tkt_type == types.TICKET_EADDR_CHANGE:
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
        he.Txt(desc_usr_code),
        he.Str(usr.usr_code)
    ]
    for txt, inpt in get_txt_and_input(ctx, tables.LocalAuth.loc_password):
        trs += [txt, inpt]
    trs += [
        he.Txt("word_confirmation"),
        input_confirm
    ]
    table = he.mktable(
        ((c, ) for c in trs),
        id_="table-password-change",
        class_="table-form"
    )
    img = base.static_img(
        "checkmark",
        "word_send",
        js=f"ticket_password_change('{tkt.tkt_value}')",
        class_="submit"
    )
    div = he.Div(
        table,
        img,
        class_="box"
    )
    return base.page(ctx, "page_title_password_change", div)


def _page_eaddr_change(
        ctx: context.Context,
        tkt: tables.Ticket
) -> fa.Response:
    assert tkt.tkt_usr is not None
    usr = queries.get_usr(ctx.dbs, tkt.tkt_usr)
    assert usr is not None

    # update usr
    usr = ctx.dbs.query(
        tables.Usr
    ).where(
        tables.Usr.usr_id == usr.usr_id
    ).first()
    assert usr is not None
    usr.usr_eaddr = tkt.tkt_eaddr

    # delete ticket
    ctx.dbs.query(
        tables.Ticket
    ).where(
        tables.Ticket.tkt_id == tkt.tkt_id
    ).delete()

    msg = he.Txt("succ_eaddr_changed")
    return base.page(ctx, "page_title_eaddr_change", msg)


def _page_account_creation(
        ctx: context.Context,
        tkt: tables.Ticket
) -> fa.Response:
    input_confirm = he.Input(type_="password", id_="loc_password_confirm")
    desc_usr_eaddr = desc.col_desc("usr_eaddr")
    trs = [he.Txt(desc_usr_eaddr), he.Str(tkt.tkt_eaddr)]
    for txt, element in get_txt_and_input(
        ctx,
        tables.Usr.usr_code,
        tables.Usr.usr_fst_name,
        tables.Usr.usr_name,
        tables.LocalAuth.loc_password
    ):
        trs += [txt, element]
    trs += [he.Txt("word_confirmation"), input_confirm]
    table = he.mktable(((cell, ) for cell in trs), class_="table-form")
    a_send = base.static_img(
        "checkmark",
        "word_send",
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
    return base.page(ctx, "page_title_authentication_account_creation", div)
