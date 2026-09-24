from webamc.www.all import *
from webamc.www.db import util as www_db_util
from webamc.www.auth.oper import login_cas


def page(ctx: context.Context) -> fa.Response:
    elements = list()

    # cas authentication
    if config.CONFIG["auth_cas_enabled"]:
        href = login_cas.get_cas_client().get_login_url()
        elements += [
            he.H3(he.Txt("header_authentication_cas")),
            he.A(he.Str(" " + config.CONFIG["cas_server_name"]), href=href)
        ]

    # local authentication
    if config.CONFIG["auth_local_enabled"]:
        cols = [
            "loc_login",
            "loc_password"
        ]
        trs = [
            he.Tr(he.Td(txt), he.Td(element))
            for txt, element in www_db_util.get_txt_and_input(ctx, cols)
        ]
        a_conn = base.static_img(
            "checkmark",
            "verb_send",
            js="auth_send_login_local()",
            class_="submit"
        )
        table = he.Table(
            *trs,
            id_="table-login-local",
            class_="table-form"
        )
        div = he.Div(
            table,
            a_conn,
            class_="box"
        )
        h3 = he.H3(he.Txt("header_authentication_local"))
        elements += [h3, div]

        a_send = base.static_img(
            "checkmark",
            "verb_send",
            js="auth_send_password_change()",
            class_="submit"
        )
        trs = [
            he.Tr(he.Td(txt), he.Td(element))
            for txt, element in
            www_db_util.get_txt_and_input(ctx, ["usr_eaddr"])
        ]
        table = he.Table(
            *trs,
            id_="table-password-change",
            class_="table-form"
        )
        div = he.Div(
            table,
            a_send,
            class_="box"
        )
        h3 = he.H3(he.Txt("header_authentication_password_change"))
        elements += [h3, div]

    # account creation
    if config.CONFIG["auth_account_creation_enabled"]:
        a_create = base.static_img(
            "checkmark",
            "verb_send",
            js="auth_send_creation()",
            class_="submit"
        )
        cols = [
            "usr_eaddr"
        ]
        trs = [
            he.Tr(he.Td(txt), he.Td(element))
            for txt, element in www_db_util.get_txt_and_input(ctx, cols)
        ]
        table = he.Table(
            *trs,
            class_="table-form"
        )
        div = he.Div(
            table,
            a_create,
            class_="box",
            id_="table-creation"
        )
        h3 = he.H3(he.Txt("header_authentication_account_creation"))
        elements += [h3, div]

    return base.page(
        ctx,
        "page_title_authentication",
        he.ElementList(*elements)
    )
