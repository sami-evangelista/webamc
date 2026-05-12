#!/usr/bin/env python3

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
        return fa.responses.HTMLResponse("Examen introuvable.")

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

    trs: list[he.Element] = list()
    exam_not_start = monitoring_data['exam_status'] == "upcoming"
    tr_all = []
    
    # table header with 5 columns
    if exam_not_start:
        input_all = he.Input(
            type_="checkbox", 
            id_="checkbox_all", 
            onclick="exam_select_all_registrations()"
        )
        tr_all.append(he.Td(input_all))

    
    tr_all.extend([
        he.Td(he.Str("Login")),
        he.Td(he.Str("Student")),
        he.Td(he.Str("Progress")),
        he.Td(he.Str("Status"))
    ])
    trs.append(he.Tr(*tr_all))

    # rows generation
    for student in monitoring_data["students"]:
        student_name = fmt.fmt_name(student['usr_fst_name'], student['usr_name'])
        
        row_cells = []
        
        # checkbox using reg_id for deletion actions
        if exam_not_start:
            input_check = he.Input(
                type_="checkbox",
                id_=f"checkbox_{student['reg_id']}",
                class_="checkbox_registration"
            ).set_data("reg_id", str(student['reg_id']))
            row_cells.append(he.Td(input_check))
        
        # status with color coding
        s_color = student_colors.get(student["status"], "black")
        status_element = he.Span(
            he.Str(student["status"]), 
            style=f"color: {s_color}; font-weight: bold;"
        )
        
        # progress bar logic
        answered = student["answered_count"]
        total = student["total_questions"]
        percent = int((answered / total) * 100) if total > 0 else 0
        
        # green if 100%, blue otherwise
        bar_color = "#28a745" if percent == 100 else "#007bff"
        
        progress_fill = he.Div(
            style=f"width: {percent}%; height: 100%; background-color: {bar_color}; transition: width 0.3s;"
        )
        progress_bg = he.Div(
            progress_fill,
            style="width: 100px; height: 12px; background-color: #e9ecef; border-radius: 4px; overflow: hidden; display: inline-block; vertical-align: middle; border: 1px solid #ccc;"
        )
        progress_text = he.Span(
            he.Str(f" {answered}/{total}"), 
            style="font-size: 0.85em; margin-left: 8px; vertical-align: middle; color: #555;"
        )
        progress_element = he.Div(progress_bg, progress_text)

        # build row
        row_cells.extend([
            he.Td(he.Str(student["usr_login"])),
            he.Td(he.Str(student_name)),
            he.Td(progress_element),
            he.Td(status_element)
        ])

        trs.append(he.Tr(*row_cells))

    # assemble page elements
    elements: list[he.Element] = list()
    
    # global exam status
    e_color = exam_colors.get(monitoring_data['exam_status'], "black")
    header_status = he.H3(
        he.Str(f"Statut de l'épreuve : {monitoring_data['exam_status']}"), 
        style=f"color: {e_color}; margin-bottom: 15px;"
    )
    elements.append(header_status)
    
    # registration count
    txt = lang.txt("param_seq_users_registered") % str(len(monitoring_data["students"]))
    elements.append(he.P(he.Str(txt)))

    if exam_not_start and len(monitoring_data["students"]) > 0:
        img_delete = base.static_img("trash", "verb_delete", js="exam_delete_registrations()")
        elements.append(img_delete)
        
    
    # data table
    if len(monitoring_data["students"]) > 0:
        elements.append(he.Table(*trs, class_="table-form"))
        
    return fa.responses.HTMLResponse(str(he.ElementList(*elements)))