#!/usr/bin/env python3

from webamc.www.all import *
from webamc.www.db import util as www_db_util


def page(ctx: context.Context) -> he.Element:
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
    table = he.Table(*trs)
    result = he.Div(
        table,
        a_create,
        class_="box",
        id_="table-creation"
    )
    return result
