import typing as tp

from webamc.www.all import *
from webamc.db import tables, queries
from webamc.util import fmt

def page(ctx: context.Context, exam_id: int | None) -> fa.Response:
    
    # getting exams with their titles
    exams = ctx.dbs.query(
        tables.Exam, tables.Item
    ).join(
        tables.Item, tables.Exam.exm_mcq == tables.Item.itm_id
    ).order_by(
        tables.Exam.exm_start.desc()
    ).all()
    
    exam_options: list[he.Element] = [
        he.Option(he.Str("Sélectionnez un examen..."), value="")
    ]
    
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
    elements: list[he.Element] = [
        he.H1(he.Str("Tableau de bord des statistiques")),
        he.Div(he.Str("1. Choisir un examen :")),
        select_exam,
        he.Br(), he.Br()
    ]


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
            he.Option(he.Str("Sélectionnez une question..."), value="")
        ]

        for i, qst in enumerate(questions):
            label = chr(65 + i) if i < 26 else str(i + 1)
            qst_options.append(
                he.Option(
                    he.Str(f"Question {label}"),
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
            style_="max-width: 600px; max-height: 400px; margin: 0 auto;"
        )

        # containers for question image and choices
        qst_image_element = he.Img(
            id_="qst_image", 
            src="", 
            style_="display: none; max-width: 100%; border: 1px solid #ccc; margin-top: 20px;"
        )
        choices_container = he.Div(id_="choices_container", style_="margin-top: 20px;")
        
        # adding elements to page
        elements.extend([
            he.Hr(),
            he.Div(he.Str("2. Choisir une question :")),
            select_qst,
            canvas_container,
            qst_image_element,
            choices_container
        ])

    # adding js scripts
    elements.extend([
        he.Script(src="https://cdn.jsdelivr.net/npm/chart.js")
    ])
    
    result = he.ElementList(*elements)
    
    return base.page(ctx, "page_title_stats", result)