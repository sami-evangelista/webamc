import typing as tp

from webamc.www.all import *
from webamc.db import tables, queries
from webamc.util import fmt

def page(ctx: context.Context, exam_id: int | None) -> fa.Response:

    elements: list[he.Element] = []

    # getting exams with their titles
    exams = ctx.dbs.query(
        tables.Exam, tables.Item
    ).join(
        tables.Item, tables.Exam.exm_mcq == tables.Item.itm_id
    ).order_by(
        tables.Exam.exm_start.desc()
    ).all()
    
    exam_options: list[he.Element] = [
        he.Option(he.Str(lang.txt("stats_select_exam")), value="")
    ]    

    ########## MCQ Overview (Third diagram) ########

    overview_exam_options: list[he.Element] = [
        he.Option(he.Str("Sélectionner un examen pour la vue d'ensemble"), value="")
    ]
    
    # rebuilding the list of options using the fetched exams
    for exm, itm in exams:
        overview_exam_options.append(
            he.Option(
                he.Str(f"{itm.itm_title} (Date: {exm.exm_start.strftime('%d/%m/%Y')})"), 
                value=f"{exm.exm_id}"
            )
        )

    # exam selector dropdown for the overview chart
    select_overview_exam = he.Select(
        *overview_exam_options,
        id_="overview_exam_selector",
        class_="box",
        onchange="loadMcqOverview(this.value)"
    )

    # chart container with fixed size
    overview_canvas_container = he.Div(
        he.Canvas(id_="mcq_overview_chart"),
        style_="max-width: 800px; height: 400px; margin: 20px auto;"
    )

    # adding elements to page
    elements.extend([
        he.Hr(style_="margin: 40px 0; border: 2px solid #eee;"),
        he.H2(he.Str("Vue d'ensemble globale du QCM")),
        he.Div(he.Str("Choisir un examen :")),
        select_overview_exam,
        overview_canvas_container
    ])

    ########## (first diagram) ########

    
    
    for exm, itm in exams:
        # selecting current exam
        is_selected = (exam_id == exm.exm_id)
        opt = he.Option(
            he.Str(f"{itm.itm_title} (Date: {exm.exm_start.strftime('%d/%m/%Y')})"), 
            value=f"{exm.exm_id}"
        )
        if is_selected:
            opt.set_attr("selected", "selected")
            
        exam_options.append(opt)

    # exam selector dropdown
    select_exam = he.Select(
        *exam_options,
        id_="exam_selector",
        class_="box",
        onchange="window.location.href = '?exam_id=' + this.value;"
    )

    # building page
    elements.extend([
        he.H1(he.Str(lang.txt("stats_title"))),
        he.Div(he.Str(lang.txt("stats_choose_exam"))),
        select_exam,
        he.Br(), he.Br()
    ])


    # question selector and chart
    if exam_id is not None:
        
        # getting exam object to find mcq_id
        exam = ctx.dbs.query(tables.Exam).filter(tables.Exam.exm_id == exam_id).first()
        
        if exam is not None:
            # getting questions for this mcq
            questions = queries.get_exam_questions(ctx.dbs, exam.exm_mcq)
        else:
            questions = []

        qst_options: list[he.Element] = [
            he.Option(he.Str(lang.txt("stats_select_qst")), value="")
        ]

        for i, qst in enumerate(questions):
            label = chr(65 + i) if i < 26 else str(i + 1)
            qst_options.append(
                he.Option(
                    he.Str(f"{lang.txt('stats_qst_prefix')} {label}"),
                    value=f"{qst.qst_id}"
                )
            )

        select_qst = he.Select(
            *qst_options,
            id_="qst_selector",
            class_="box",
            onchange="handleQuestionChange(this.value)"
        )
        
        # chart container with fixed size
        canvas_container = he.Div(
            he.Canvas(id_="chart"),
            style_="max-width: 600px; max-height: 400px; margin: auto;"
        )
        
        qst_image_element = he.Img(
            id_="qst_image", 
            src="", 
            style_="display: none; max-width: 100%; border: 1px solid #ccc; margin-bottom: 20px;"
        )
        choices_container = he.Div(
            id_="choices_container", 
            style_="display: flex; flex-direction: column; align-items: flex-start; text-align: left;"
        )

        choices_container.set_attr("data-title", lang.txt("stats_answers_detail"))
        choices_container.set_attr("data-answer", lang.txt("stats_answer_prefix"))
        
        left_column = he.Div(
            qst_image_element,
            choices_container
        )

        dashboard_flex_layout = he.Div(
            left_column,
            canvas_container,
            style_="display: flex; flex-direction: row; justify-content: space-between; align-items: flex-start; gap: 20px; margin-top: 20px;"
        )

        # adding elements to page
        elements.extend([
            he.Hr(),
            he.Div(he.Str(lang.txt("stats_choose_qst"))),
            select_qst,
            dashboard_flex_layout
        ])

    ########## graphe evolution (Second diagram) ########

    elements.extend([
        he.Hr(style_="margin: 40px 0; border: 2px solid #eee;"),
        he.H2(he.Str(lang.txt("stats_evo_title")))
        ])

    students = ctx.dbs.query(tables.Usr).order_by(
            tables.Usr.usr_name.asc(),
            tables.Usr.usr_fst_name.asc()
        ).all()
        
    student_options = [he.Option(he.Str(lang.txt("stats_select_student")), value="")]
    for std in students:
        student_options.append(
            he.Option(he.Str(f"{std.usr_fst_name} {std.usr_name}"), value=f"{std.usr_id}")
            )

    select_student = he.Select(
        *student_options,
        id_="evo_student_selector",
        class_="box",
        onchange="triggerEvolutionChart()"
        )
    exams_and_mcqs = ctx.dbs.query(
        tables.Exam, tables.Item
    ).join(
        tables.Item, tables.Exam.exm_mcq == tables.Item.itm_id
    ).all()

    mcq_options = [he.Option(he.Str(lang.txt("stats_select_mcq")), value="")]
    seen_mcqs = set() 
    for exm, mcq in exams_and_mcqs:
        if mcq.itm_id not in seen_mcqs:
            seen_mcqs.add(mcq.itm_id)
            mcq_options.append(
                he.Option(he.Str(mcq.itm_title), value=f"{mcq.itm_id}")
                )

    select_mcq_evo = he.Select(
        *mcq_options,
        id_="evo_mcq_selector",
        class_="box",
        onchange="triggerEvolutionChart()"
        )

    evolution_canvas_container = he.Div(
        he.Canvas(id_="evolution_chart"),
        style_="max-width: 600px; height: 500px; margin: 20px auto;"
        )

    elements.extend([
        he.Div(he.Str(lang.txt("stats_student_prefix")), select_student),
        he.Br(),
        he.Div(he.Str(lang.txt("stats_mcq_prefix")), select_mcq_evo),
        evolution_canvas_container
        ])



    
    # adding js scripts
    elements.extend([
        he.Script(src="https://cdn.jsdelivr.net/npm/chart.js"),
        he.Script(src="/static?file_name=stats.js")  
    ])

    result = he.ElementList(*elements)

    
    return base.page(ctx, "page_title_stats", result)