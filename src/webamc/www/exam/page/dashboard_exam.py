from webamc.www.all import *
from webamc.db import queries
from webamc.util import fmt
from webamc.www.exam import router


def page(
        ctx: context.Context,
        args: router.args_page_dashboard_exam_t
) -> fa.Response:

    exam_id = args["exm_id"]
    monitoring_data = queries.get_exam_monitoring(ctx.dbs, exam_id)

    if not monitoring_data:
        return fa.responses.HTMLResponse(lang.txt("error_exam_not_found"))

    # color configuration
    exam_colors = {
        "upcoming": "#0056b3",
        "in progress": "#28a745",
        "finished": "#6c757d"
    }

    student_colors = {
        "online": "green",
        "not started": "red",
        "inactive (> 5 min)": "orange"
    }

    # translation mapping for dynamic database statuses
    translated_status = {
        "upcoming": lang.txt("status_upcoming"),
        "in progress": lang.txt("status_in_progress"),
        "finished": lang.txt("status_finished"),
        "online": lang.txt("status_online"),
        "not started": lang.txt("status_not_started"),
        "inactive (> 5 min)": lang.txt("status_inactive")
    }

    trs: list[he.Element] = list()
    raw_exam_status = monitoring_data.get("exam_status", "")
    exam_not_start = raw_exam_status == "upcoming"
    tr_all = []

    # table header with translated columns

    if exam_not_start:
        input_all = he.Input(
            type_="checkbox",
            id_="checkbox_all",
            onclick="exam_select_all_registrations()"
        )
        tr_all.append(he.Td(input_all))

    tr_all.extend([
        he.Td(he.Txt("name_login")),
        he.Td(he.Txt("name_student")),
        he.Td(he.Str("Score")),  # will be put in lang later
        he.Td(he.Txt("name_progress")),
        he.Td(he.Txt("name_status"))
    ])
    trs.append(he.Tr(*tr_all))

    # rows generation
    for student in monitoring_data["students"]:
        student_name = fmt.fmt_name(student["usr_fst_name"],
                                    student["usr_name"])

        row_cells = []

        # checkbox using reg_id for deletion actions
        if exam_not_start:
            input_check = he.Input(
                type_="checkbox",
                id_=f"checkbox_{student['reg_id']}",
                class_="checkbox_registration"
            ).set_data(
                "reg_id", str(student['reg_id'])
            )

            row_cells.append(he.Td(input_check))

        # status with color coding and translation
        raw_student_status = student["status"]
        s_color = student_colors.get(raw_student_status, "black")
        display_student_status = translated_status.get(raw_student_status,
                                                       raw_student_status)

        status_element = he.Span(
            he.Str(display_student_status),
            style=f"color: {s_color}; font-weight: bold;"
        )

        # progress bar logic
        answered = student["answered_count"]
        total = student["total_questions"]
        percent = int((answered / total) * 100) if total > 0 else 0

        # green if 100%, blue otherwise
        bar_color = "#28a745" if percent == 100 else "#007bff"

        style = (
            f"width: {percent}%; height: 100%; background-color: {bar_color}; "
            "transition: width 0.3s;"
        )
        progress_fill = he.Div(
            style=style
        )
        style = (
            "width: 100px; height: 12px; background-color: #e9ecef; "
            "border-radius: 4px; overflow: hidden; display: inline-block; "
            "vertical-align: middle; border: 1px solid #ccc;"
        )
        progress_bg = he.Div(
            progress_fill,
            style=style
        )
        style = (
            "font-size: 0.85em; margin-left: 8px; vertical-align: middle; "
            "color: #555;"
        )
        progress_text = he.Span(
            he.Str(f" {answered}/{total}"),
            style=style
        )
        progress_element = he.Div(progress_bg, progress_text)

        # build row
        row_cells.extend([
            he.Td(he.Str(student["usr_login"])),
            he.Td(he.Str(student_name)),
            he.Td(he.Str(str(student["score"]))),
            he.Td(progress_element),
            he.Td(status_element)
        ])
        trs.append(he.Tr(*row_cells))

    # assemble page elements
    elements: list[he.Element] = list()

    # global exam status translated
    raw_exam_status = monitoring_data['exam_status']
    e_color = exam_colors.get(raw_exam_status, "black")
    display_exam_status = translated_status.get(
        raw_exam_status,
        raw_exam_status
    )

    header_status = he.H3(
        he.Str(lang.txt("info_exam_status") % display_exam_status),
        style=f"color: {e_color}; margin-bottom: 15px;"
    )
    elements.append(header_status)

    # registration count
    txt = (
        lang.txt("param_seq_users_registered")
        % str(len(monitoring_data["students"]))
    )
    elements.append(he.P(he.Str(txt)))

    # export button
    if len(monitoring_data["students"]) > 0:
        style = (
            "margin-bottom: 15px; display: inline-block; "
            "background-color: #28a745; color: white; padding: 8px 12px; "
            "text-decoration: none; border-radius: 4px;"
        )
        btn_export = he.A(
            he.Str("Exporter les notes"),
            href=f"../oper/export-scores?exm_id={exam_id}",
            class_="btn btn-primary",
            style=style
        )
        elements.append(btn_export)

    if exam_not_start and len(monitoring_data["students"]) > 0:
        img_delete = base.static_img(
            "trash",
            "verb_delete",
            js="exam_delete_registrations()"
        )
        elements.append(img_delete)

    # data table
    if len(monitoring_data["students"]) > 0:
        elements.append(he.Table(*trs, class_="table-form"))

    return fa.responses.HTMLResponse(str(he.ElementList(*elements)))
