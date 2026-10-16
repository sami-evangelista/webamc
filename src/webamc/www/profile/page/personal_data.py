from webamc.db import queries, util as db_util, tables
from webamc.www.all import *
from webamc.www.db import util as www_db_util


def page(ctx: context.Context) -> he.Element:
    def get_val(c: types.db_col_t) -> types.db_base_val_t:
        result = getattr(usr, db_util.get_col_name(c))
        return tp.cast(types.db_base_val_t, result)

    usr = queries.get_usr(ctx.dbs, session.usr_id(ctx))
    assert usr is not None

    trs = list()
    for txt, attr in www_db_util.get_attributes(
        ctx,
        get_val,
        tables.Usr.usr_code,
        tables.Usr.usr_fst_name,
        tables.Usr.usr_name,
        tables.Usr.usr_eaddr,
        updatable=False
    ):
        trs += [he.Tr(he.Td(txt)), he.Tr(he.Td(attr))]
    input_eaddr = www_db_util.get_col_input_type(ctx, "usr_eaddr").element()
    input_eaddr["placeholder"] = lang.txt("seq_enter_new_eaddr")
    a_send = base.static_img(
        "mail",
        "word_send",
        js="profile_send_eaddr_change()"
    )
    trs.append(he.Tr(he.Td(input_eaddr), he.Td(a_send)))
    result = he.Table(*trs, class_="table-form")
    return result
