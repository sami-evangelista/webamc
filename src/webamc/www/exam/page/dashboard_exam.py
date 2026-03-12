#!/usr/bin/env python3

from webamc.www.all import *
from webamc.db import queries
from webamc.util import fmt
from webamc.www.exam import router


def page(
        ctx: context.Context,
        args: router.args_page_dashboard_exam_t
) -> fa.Response:
    trs: list[he.Element] = list()
    exam = router._get_exam(ctx, args["exm_id"])[2]
    registrations = sorted(
        queries.get_exam_registrations(ctx.dbs, exam.exm_id),
        key=lambda usr_reg: (usr_reg[0].usr_name, usr_reg[0].usr_fst_name)
    )

    # first row with image links
    input_all = he.Input(
        type_="checkbox",
        id_="checkbox_all",
        onclick="exam_select_all_registrations()"
    )
    img_delete = base.static_img(
        "trash",
        "verb_delete",
        js="exam_delete_registrations()"
    )
    tr_all = he.Tr(
        he.Td(input_all),
        he.Td(img_delete)
    )
    trs.append(tr_all)
    for usr, reg in registrations:
        name = fmt.fmt_name(usr.usr_fst_name, usr.usr_name)
        input_check = he.Input(
            type_="checkbox",
            id_=f"checkbox_{reg.reg_id}",
            class_="checkbox_registration"
        ).set_data("reg_id", str(reg.reg_id))
        tr = he.Tr(
            he.Td(input_check),
            he.Td(he.Str(name))
        )
        trs.append(tr)

    elements: list[he.Element] = list()
    txt = lang.txt("param_seq_users_registered") % str(len(registrations))
    p = he.P(he.Str(txt))
    elements.append(p)
    if len(registrations) > 0:
        elements.append(he.Table(*trs, class_="table-form"))
    return fa.responses.HTMLResponse(str(he.ElementList(*elements)))
