from webamc.www.all import *
from webamc.www.exam import util as www_exam_util


def page(ctx: context.Context, exm_id: int) -> he.Element:

    exams, select_exams = www_exam_util.get_exams_select(ctx)
    if len(exams) == 0:
        return he.Txt("exam_info_no_exam_available")

    trs = list()

    # select with user exams
    select_exams["onchange"] = "exam_dashboard_select()"
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
