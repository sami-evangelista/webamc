from webamc.db import queries, util as db_util, tables
from webamc.www.all import *
from webamc.www.db import util as www_db_util


def page(ctx: context.Context) -> fa.Response:
    def get_val(c: types.db_col_t) -> types.db_base_val_t:
        result = getattr(usr, db_util.get_col_name(c))
        return tp.cast(types.db_base_val_t, result)
    def get_rights(rights: list[types.usr_right_t]) -> he.Element:
        if not session.has_submission_right(ctx):
            return he.Empty()
        elements: list[he.Element] = list()
        rmap: dict[types.usr_right_t, types.txt_t] = {
            types.USR_RIGHT_VIEW: "word_view",
            types.USR_RIGHT_SUBMIT: "word_submission"
        }
        for i, r in enumerate(rights):
            if i > 0:
                elements.append(he.Str(" + "))
            elements.append(he.Txt(rmap[r]))
        return he.ElementList(*elements)

    usr = queries.get_usr(ctx.dbs, session.usr_id(ctx))
    assert usr is not None

    trs: list[he.Element] = list()
    for txt, attr in www_db_util.get_attributes(
        ctx,
        get_val,
        tables.Usr.usr_code,
        tables.Usr.usr_fst_name,
        tables.Usr.usr_name,
        tables.Usr.usr_eaddr,
        updatable=False
    ):
        trs += [txt, attr]
    input_eaddr = www_db_util.get_col_input_type(ctx, "usr_eaddr").element()
    input_eaddr["placeholder"] = lang.txt("seq_enter_new_eaddr")
    a_send = base.static_img(
        "mail",
        "word_send",
        js="profile_send_eaddr_change()"
    )
    trs += [he.mktable([[input_eaddr, a_send]])]

    # table containing user groups
    groups: dict[int, tuple[tables.Grp, list[types.usr_right_t]]] = dict()
    for grp, usr_grp in queries.get_grps(ctx.dbs, session.usr_id(ctx)):
        groups.setdefault(grp.grp_id, (grp, list()))[1].append(
            usr_grp.ugp_right
        )
    trs_rights = list()
    if session.has_submission_right(ctx):
        trs_rights.append([he.Empty(), he.Txt("word_rights")])
    for grp, rights in groups.values():
        trs_rights += [
            [
                he.Div(he.Str(grp.grp_name), class_="group-name"),
                get_rights(rights)
            ]
        ]
    table_rights = he.mktable(trs_rights)

    trs += [base.field_label(he.Txt("seq_my_groups")), table_rights]
    table = he.mktable(((tr, ) for tr in trs), class_="table-form")
    return base.page(ctx, "profile", table)
