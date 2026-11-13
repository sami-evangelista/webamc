from webamc.www.all import *
from webamc.db import tables, queries
from webamc.util import fmt


def page(ctx: context.Context, exm_id: int) -> he.Element:
    def format_exam(exam: tables.Exam) -> str:
        title = exam.exm_title
        return title + " (" + fmt.fmt_datetime(exam.exm_start) + ")"

    exams = list(queries.get_usr_exams(ctx.dbs, session.usr_id(ctx)))
    if exams == list():
        return he.Txt("exam_info_no_exam_available")

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
    trs.append([he.Txt("exam_select_an_exam"), select_exams])

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
