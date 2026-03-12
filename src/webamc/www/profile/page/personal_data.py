#!/usr/bin/env python3

from webamc.www.all import *
from webamc.db import queries
from webamc.www.db import util as www_db_util


def page(ctx: context.Context) -> he.Element:
    def get_val(col_name: str) -> types.db_base_val_t:
        return tp.cast(types.db_base_val_t, getattr(usr, col_name))

    usr = queries.get_usr(ctx.dbs, session.usr_id(ctx))
    assert usr is not None

    cols = [
        "usr_code",
        "usr_fst_name",
        "usr_name",
        "usr_eaddr"
    ]
    attrs = www_db_util.get_attributes(ctx, cols, get_val, updatable=False)
    trs = [he.Tr(he.Td(txt), he.Td(attr)) for txt, attr in attrs]
    input_eaddr = www_db_util.get_col_input_type(ctx, "usr_eaddr").element()
    input_eaddr["placeholder"] = lang.txt("seq_enter_new_eaddr")
    a_send = base.static_img(
        "mail", "verb_send", js="profile_send_eaddr_change()"
    )
    trs += [
        he.Tr(he.Td(), he.Td(input_eaddr)),
        he.Tr(he.Td(), he.Td(a_send))
    ]
    result = he.Table(*trs, class_="table-form")
    return result
