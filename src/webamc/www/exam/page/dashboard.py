from webamc.www.all import *
from webamc.db import tables, queries
from webamc.util import fmt


def page(ctx: context.Context, exm_id: int) -> he.Element:
    def format_exam(exam: tables.Exam) -> str:
        title = exam.exm_title
        return title + " (" + fmt.fmt_datetime(exam.exm_start) + ")"

    exams = list(queries.get_usr_exams(ctx.dbs, session.usr_id(ctx)))

    trs = list()

    # select with exams
    select_exams = he.Select(
        he.Option(he.Str("-"), value=""),
        *[he.Option(he.Str(format_exam(exam)), value=exam.exm_id)
          for item, exam in exams],
        id_="exm_id",
        onchange="exam_dashboard_select()"
    ).set_data(
        "type", "integer"
    )
    trs.append([he.Txt("seq_select_an_exam"), select_exams])

    # select with groups
    query_grps = queries.get_submit_grps(ctx.dbs, session.usr_id(ctx))
    grps = list(query_grps)
    opts = [
        he.Option(he.Str(grp.grp_name), value=grp.grp_id) for grp in grps
    ]
    select_grp = he.Select(
        he.Option(he.Str("-"), value=""),
        *opts,
        id_="grp_id",
        onchange="exam_register()"
    ).set_data(
        "type", "integer"
    )
    trs.append([he.Txt("seq_select_a_group_to_register"), select_grp])

    # select with users
    grps_ids = set(grp.grp_id for grp in grps)
    query_usrs = queries.get_grps_usrs(ctx.dbs, grps_ids, types.USR_RIGHT_VIEW)
    opts = [
        he.Option(
            he.Str(fmt.fmt_name(usr.usr_fst_name, usr.usr_name, False)),
            value=usr.usr_id
        )
        for usr in query_usrs
    ]
    select_usr = he.Select(
        he.Option(he.Str("-"), value=""),
        *opts,
        id_="usr_id",
        onchange="exam_register()"
    ).set_data(
        "type", "integer"
    )
    trs.append([he.Txt("seq_select_a_user_to_register"), select_usr])

    table = he.mktable(trs, class_="table-form")

    # div containing inputs
    div_inputs = he.Div(table, id_="div-exam-fields", class_="box")

    # check if an exam id has been passed trough the url
    script: he.Element = he.Empty()
    if any(exam.exm_id == exm_id for _, exam in exams):
        js = f"$('#exm_id').val({exm_id});"
        js += "\nexam_dashboard_select();"
        script = he.Script(js)

    # empty div containing the result
    div_exam = he.Div(id_="div-exam-dashboard")

    result = he.ElementList(
        div_inputs,
        div_exam,
        script
    )
    return result
