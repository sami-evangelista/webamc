#!/usr/bin/env python3

from webamc.www.all import *
from webamc.www.db import util as www_db_util


def page(ctx: context.Context) -> he.Element:
    a_send = base.static_img(
        "checkmark",
        "verb_send",
        js="auth_send_password_change()",
        class_="submit"
    )
    trs = [
        he.Tr(he.Td(txt), he.Td(element))
        for txt, element in www_db_util.get_txt_and_input(ctx, ["usr_eaddr"])
    ]
    table = he.Table(
        *trs,
        id_="table-password-change"
    )
    result = he.Div(
        table,
        a_send,
        class_="box"
    )
    return result
