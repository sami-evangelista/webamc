#!/usr/bin/env python3

from webamc.www.all import *
from webamc.db import tables, queries
from webamc.util import fmt
from webamc.www.exam import router


def page(
        ctx: context.Context,
        **kwargs: tp.Unpack[router.args_page_exam_t]
) -> he.Element:
    def format_exam(
            item: tables.Item,
            mcq: tables.Mcq,
            exam: tables.Exam
    ) -> str:
        title = item.itm_title if item.itm_title is not None else "???"
        return title + " (" + fmt.fmt_datetime(exam.exm_start) + ")"

    exams = list(queries.get_usr_exams(ctx.dbs, session.usr_id(ctx)))
    
    exm_id = kwargs.get("exm_id")
    select_exams = he.Select(
        he.Option(he.Str(lang.txt("seq_select_an_exam")), value=""),
        *[he.Option(he.Str(format_exam(mcq, item, exam)), value=exam.exm_id)
          for item, mcq, exam in exams],
        id_="exm_id",
        onchange="exam_dashboard_select()"
    )

    # select with groups
    select_grp = he.Select(
        *[he.Option(he.Str(grp.grp_name), value=grp.grp_id)
          for grp in queries.get_submit_grps(
                  ctx.dbs, session.usr_id(ctx)
          )],
        id_="grp_id"
    )
    img_add = base.static_img(
        "group-add",
        title="verb_add",
        js="exam_register_group()"
    )
    table = he.Table(
        he.Tr(he.Td(select_grp), he.Td(img_add)),
        class_="table-form"
    )

    # div containing inputs
    div_inputs = he.Div(
        select_exams,
        table,
        class_="box"
    )

    # check if an exam id has been passed trough the url
    script: he.Element = he.Empty()
    if any(exam.exm_id == exm_id for _, _, exam in exams):
        js = f"$('#exm_id').val({exm_id});"
        js += "\nexam_dashboard_select();"
        script = he.Script(js)

    # empty div containing the result
    div_exam = he.Div(id_="exam_dashboard")

    result = he.ElementList(
        div_inputs,
        div_exam,
        script
    )
    return result
