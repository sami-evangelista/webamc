import random

from webamc.www.all import *
from webamc.db import queries
from webamc.util import fmt


def page(
        ctx: context.Context,
        args: types.args_route_exam_exam_t
) -> fa.Response:

    exam_id = args["exm_id"]
    monitoring_data = queries.get_exam_monitoring(ctx.dbs, exam_id)

    if not monitoring_data:
        return fa.responses.HTMLResponse(lang.txt("err_exam_not_found"))

    trs: list[list[he.Element]] = list()
    exam_status: types.exam_status_t = monitoring_data.get(
        "status", "upcoming"
    )
    exam_not_started = exam_status == "upcoming"
    exam_finished = exam_status == "finished"

    # table header
    tr_all: list[he.Element] = []
    if exam_not_started:
        input_all = he.Input(
            type_="checkbox",
            id_="checkbox_all",
            onclick="exam_select_all_registrations()"
        )
        tr_all += [input_all]
    tr_all += [
        he.Txt("word_student"),
        he.Txt("word_score"),
        he.Txt("word_progress"),
        he.Txt("word_status")
    ]
    trs.append(tr_all)

    # table rows generation
    for student in monitoring_data["students"]:
        student_name = fmt.fmt_name(
            student["usr_fst_name"],
            student["usr_name"],
            False
        )
        status = student["status"]
        tds = []

        # checkbox using reg_id for deletion actions
        if exam_not_started:
            input_check = he.Input(
                type_="checkbox",
                id_=f"checkbox_{student['reg_id']}",
                class_="checkbox_registration"
            ).set_data(
                "reg_id", str(student['reg_id'])
            )
            tds.append(input_check)

        # student status
        txt_status = tp.cast(
            types.txt_t,
            f"seq_exam_student_status_{status.replace('-', '_')}"
        )
        cls_status = f"student-status-{student['status']}"
        span_status = he.Span(he.Txt(txt_status), class_=cls_status)

        # progress bar logic
        answered = student["answered_count"]
        total = student["total_questions"]
        total = 43
        answered = random.randint(0, total)
        progress = he.Progress(
            max_=str(total),
            value=str(answered)
        )

        tds += [
            he.Str(student_name),
            he.Str(str(student["score"])),
            progress,
            span_status
        ]
        trs.append(tds)

    # assemble page elements
    elements: list[he.Element] = list()

    # table with exam general informations and buttons
    exam_status = monitoring_data["status"]
    txt_status = tp.cast(
        types.txt_t,
        f"seq_exam_status_{exam_status.replace('-', '_')}"
    )
    cls_status = f"exam-status-{exam_status}"
    span_exam_status = he.Span(he.Txt(txt_status), class_=cls_status)
    str_no_students = he.Str(str(len(monitoring_data["students"])))
    trs_exam_status: list[list[he.Element]] = [
        [he.Txt("seq_exam_status"), span_exam_status],
        [he.Txt("seq_users_registered"), str_no_students]
    ]
    buttons: list[he.Element] = list()
    if exam_not_started and len(monitoring_data["students"]) > 0:
        btn = base.static_img(
            "trash",
            "seq_delete_selected_registrations",
            js="exam_delete_registrations()"
        )
        buttons.append(btn)
    if exam_finished or True:
        btn = base.static_img(
            "doc-table",
            "seq_export_exam_scores",
            href=f"../oper/export-scores?exm_id={exam_id}"
        )
        buttons.append(btn)
    if buttons != list():        
        trs_exam_status.append([he.ElementList(*buttons), he.Empty()])
    table_exam_status = he.mktable(trs_exam_status, class_="table-form")
    elements.append(table_exam_status)

    # data table
    if len(monitoring_data["students"]) > 0:
        elements.append(he.mktable(trs, class_="table-form"))

    return fa.responses.HTMLResponse(str(he.ElementList(*elements)))
