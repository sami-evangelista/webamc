from webamc.db import tables
from webamc.www.all import *
from webamc.www.db.util import get_txt_and_input
from webamc.www.auth.oper import login_cas


def page(ctx: context.Context) -> fa.Response:
    elements = list()

    # cas authentication
    if config.CONFIG["auth_cas_enabled"]:
        href = login_cas.get_cas_client().get_login_url()
        elements += [
            he.H2(he.Txt("header_authentication_cas")),
            he.A(he.Str(" " + config.CONFIG["cas_server_name"]), href=href)
        ]

    # local authentication
    if config.CONFIG["auth_local_enabled"]:
        trs = list()
        for txt, element in get_txt_and_input(
            ctx,
            tables.LocalAuth.loc_login,
            tables.LocalAuth.loc_password
        ):
            trs += [txt, element]
        a_conn = base.static_img(
            "checkmark",
            "word_send",
            js="auth_send_login_local()",
            class_="submit"
        )
        table = he.mktable(
            ((cell, ) for cell in trs),
            id_="table-login-local",
            class_="table-form"
        )
        div = he.Div(
            table,
            a_conn,
            class_="box"
        )
        h2 = he.H2(he.Txt("header_authentication_local"))
        elements += [h2, div]

        a_send = base.static_img(
            "checkmark",
            "word_send",
            js="auth_send_password_change()",
            class_="submit"
        )
        trs = list()
        for txt, element in get_txt_and_input(ctx, tables.Usr.usr_eaddr):
            trs += [txt, element]
        table = he.mktable(
            ((cell, ) for cell in trs),
            id_="table-password-change",
            class_="table-form"
        )
        div = he.Div(
            table,
            a_send,
            class_="box"
        )
        h2 = he.H2(he.Txt("header_authentication_password_change"))
        elements += [h2, div]

    # account creation
    if config.CONFIG["auth_account_creation_enabled"]:
        a_create = base.static_img(
            "checkmark",
            "word_send",
            js="auth_send_creation()",
            class_="submit"
        )
        trs = list()
        for txt, element in get_txt_and_input(
            ctx, tables.Usr.usr_eaddr
        ):
            trs += [txt, element]
        table = he.mktable(
            ((cell, ) for cell in trs),
            class_="table-form"
        )
        div = he.Div(
            table,
            a_create,
            class_="box",
            id_="table-creation"
        )
        h2 = he.H2(he.Txt("header_authentication_account_creation"))
        elements += [h2, div]

    return base.page(
        ctx,
        "page_title_authentication",
        he.ElementList(*elements)
    )
