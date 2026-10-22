from webamc.www.all import *
from webamc.db import tables, queries
from webamc.util import fmt


def page(
        ctx: context.Context,
        **kwargs: tp.Unpack[types.args_route_exam_exam_t]
) -> he.Element:
    def format_exam(exam: tables.Exam) -> str:
        title = exam.exm_title
        return title + " (" + fmt.fmt_datetime(exam.exm_start) + ")"

    exams = list(queries.get_usr_exams(ctx.dbs, session.usr_id(ctx)))

    trs = list()

    # select with exams
    exm_id = kwargs.get("exm_id")
    select_exams = he.Select(
        he.Option(he.Str("-"), value=""),
        *[he.Option(he.Str(format_exam(exam)), value=exam.exm_id)
          for item, exam in exams],
        id_="exm_id",
        onchange="exam_dashboard_select()"
    )
    trs.append([he.Txt("seq_select_an_exam"), select_exams])

    # select with groups
    q = queries.get_submit_grps(ctx.dbs, session.usr_id(ctx))
    select_grp = he.Select(
        he.Option(he.Str("-"), value=""),
        *[he.Option(he.Str(grp.grp_name), value=grp.grp_id) for grp in q],
        id_="grp_id",
        onchange="exam_register_group()"
    )
    trs.append([he.Txt("seq_select_a_group_to_register"), select_grp])

    table = he.mktable(trs, class_="table-form")

    # div containing inputs
    div_inputs = he.Div(table, class_="box")

    # check if an exam id has been passed trough the url
    script: he.Element = he.Empty()
    if any(exam.exm_id == exm_id for _, exam in exams):
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
