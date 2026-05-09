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

    # Configuration des couleurs
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
    
    # 1. En-tête du tableau avec 4 colonnes
    input_all = he.Input(type_="checkbox", id_="checkbox_all", onclick="exam_select_all_registrations()")
    img_delete = base.static_img("trash", "verb_delete", js="exam_delete_registrations()")
    
    tr_all = he.Tr(
        he.Td(input_all),
        he.Td(he.Str("Login")),            # Nouvelle colonne en premier
        he.Td(he.Str("Étudiant")),          # Nom seul
        he.Td(he.Str("Statut de connexion"))
    )
    trs.append(tr_all)

    # 2. Remplissage des lignes
    for student in monitoring_data["students"]:
        # Séparation du nom et du login
        student_name = fmt.fmt_name(student['usr_fst_name'], student['usr_name'])
        
        input_check = he.Input(
            type_="checkbox",
            id_=f"checkbox_{student['reg_id']}",
            class_="checkbox_registration"
        ).set_data("reg_id", str(student['reg_id']))
        
        s_color = student_colors.get(student["status"], "black")
        status_element = he.Span(
            he.Str(student["status"]), 
            style=f"color: {s_color}; font-weight: bold;"
        )
        
        # 3. Création de la ligne avec le login en deuxième position
        tr = he.Tr(
            he.Td(input_check),
            he.Td(he.Str(student["usr_login"])), # Colonne Login
            he.Td(he.Str(student_name)),          # Colonne Nom
            he.Td(status_element)                # Colonne Statut
        )
        trs.append(tr)

    # Assemblage de la page
    elements: list[he.Element] = list()
    
    e_color = exam_colors.get(monitoring_data['exam_status'], "black")
    header_status = he.H3(
        he.Str(f"Statut de l'épreuve : {monitoring_data['exam_status']}"), 
        style=f"color: {e_color}; margin-bottom: 15px;"
    )
    elements.append(header_status)
    
    txt = lang.txt("param_seq_users_registered") % str(len(monitoring_data["students"]))
    elements.append(he.P(he.Str(txt)))
    
    if len(monitoring_data["students"]) > 0:
        elements.append(he.Table(*trs, class_="table-form"))
        
    return fa.responses.HTMLResponse(str(he.ElementList(*elements)))