from webamc.www.all import *
from webamc.db import tables, queries
from webamc.www import session


def page(ctx: context.Context, exam_id: int | None) -> fa.Response:

    current_usr_id = session.usr_id(ctx)
    elements: list[he.Element] = []

    dashboard_style = (
        "max-width: 1400px; margin: 0 auto; padding: 20px; color: #334155;"
    )
    header_style = (
        "margin-bottom: 30px; border-bottom: 2px solid #e2e8f0; "
        "padding-bottom: 15px;"
    )
    card_style = (
        "background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; "
        "box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05); padding: 24px; "
        "margin-bottom: 30px;"
    )
    card_header_style = (
        "display: flex; flex-wrap: wrap; justify-content: space-between; "
        "align-items: center; gap: 15px; margin-bottom: 20px; "
        "padding-bottom: 15px; border-bottom: 1px solid #f1f5f9;"
    )
    controls_group_style = (
        "display: flex; flex-wrap: wrap; align-items: center; gap: 12px; "
        "font-size: 0.9rem; color: #64748b;"
    )
    chart_container_style = (
        "position: relative; width: 100%; min-height: 500px; display: flex; "
        "justify-content: center; align-items: center;"
    )
    qst_layout_style = (
        "display: flex; flex-wrap: wrap; gap: 30px; align-items: flex-start; "
        "margin-top: 15px; justify-content: space-between;"
    )

    exams = ctx.dbs.query(
        tables.Exam, tables.Item
    ).join(
        tables.Item, tables.Exam.exm_mcq == tables.Item.itm_id
    ).filter(
        tables.Item.itm_usr == current_usr_id
    ).order_by(
        tables.Exam.exm_start.desc()
    ).all()

    # head section
    exam_options: list[he.Element] = [
        he.Option(he.Str(lang.txt("stats_select_exam")), value="")
    ]

    for exm, itm in exams:
        is_selected = exam_id == exm.exm_id
        opt = he.Option(
            he.Str(f"{itm.itm_title} ({exm.exm_start.strftime('%d/%m/%Y')})"),
            value=f"{exm.exm_id}"
        )
        if is_selected:
            opt.set_attr("selected", "selected")
        exam_options.append(opt)

    select_exam = he.Select(
        *exam_options,
        id_="exam_selector",
        class_="box",
        onchange=(
            "if(typeof loadExamDetail === 'function') "
            "{ loadExamDetail(this.value); } "
            "else { window.location.href = '?exam_id=' + this.value; }"
        )
    )

    header_section = he.Div(
        he.H1(
            he.Str(lang.txt("stats_title")),
            style_="margin: 0 0 15px 0; color: #0f172a;"
        ),
        he.Div(
            he.Str(f"{lang.txt('stats_choose_exam')} : "),
            select_exam,
            style_=controls_group_style
        ),
        style_=header_style
    )

    # card 1: questions
    card_question_detail = he.Div()
    if exam_id is not None:
        exam = ctx.dbs.query(
            tables.Exam
        ).filter(
            tables.Exam.exm_id == exam_id
        ).first()
        if exam:
            questions = queries.get_exam_questions(ctx.dbs, exam.exm_mcq)
        else:
            questions = list()

        qst_options: list[he.Element] = [
            he.Option(he.Str(lang.txt("stats_select_qst")), value="")
        ]
        for qst in questions:
            itm = queries.get_item(ctx.dbs, qst.qst_id)
            if itm and itm.itm_code:
                code_display = str(itm.itm_code)
            else:
                code_display = f"Qst {qst.qst_id}"
            qst_options.append(
                he.Option(
                    he.Str(code_display),
                    value=f"{qst.qst_id}"
                )
            )

        select_qst = he.Select(
            *qst_options,
            id_="qst_selector",
            class_="box",
            onchange="handleQuestionChange(this.value)"
        )

        qst_image_element = he.Img(
            id_="qst_image",
            src="",
            style_=(
                "display: none; width: 100%; max-height: 380px; "
                "object-fit: contain; border: 1px solid #e2e8f0; "
                "border-radius: 6px; margin-bottom: 15px; cursor: zoom-in; "
                "box-shadow: 0 2px 4px rgba(0,0,0,0.05); background: #f8fafc;"
            ),
            onclick=(
                "document.getElementById('modal_image').src=this.src; "
                "document.getElementById('image_modal').style.display='flex';"
            )
        )

        choices_container = he.Div(
            id_="choices_container",
            style_=(
                "display: flex; flex-direction: column; "
                "gap: 8px; width: 100%;"
            )
        )
        choices_container.set_attr(
            "data-title",
            lang.txt("stats_answers_detail")
        )
        choices_container.set_attr(
            "data-answer",
            lang.txt("stats_answer_prefix")
        )

        left_column = he.Div(
            qst_image_element,
            choices_container,
            style_="flex: 1.2; min-width: 360px;"
        )
        right_column = he.Div(
            he.Canvas(id_="chart"),
            style_="flex: 1.5; min-width: 400px; min-height: 450px;"
        )

        card_question_detail = he.Div(
            he.Div(
                he.H2(
                    he.Str("Détail par question"),
                    style_="margin: 0; font-size: 1.25rem; color: #1e293b;"
                ),
                he.Div(
                    he.Str(f"{lang.txt('stats_choose_qst')} : "),
                    select_qst,
                    style_=controls_group_style
                ),
                style_=card_header_style
            ),
            he.Div(left_column, right_column, style_=qst_layout_style),
            style_=card_style
        )

    # card 2: global view
    overview_exam_options: list[he.Element] = [
        he.Option(he.Str("Sélectionner un examen"), value="")
    ]
    for exm, itm in exams:
        title = f"{itm.itm_title} ({exm.exm_start.strftime('%d/%m/%Y')})"
        overview_exam_options.append(
            he.Option(he.Str(title), value=f"{exm.exm_id}")
        )
    select_overview_exam = he.Select(
        *overview_exam_options,
        id_="overview_exam_selector",
        class_="box",
        onchange="loadMcqOverview(this.value)"
    )
    select_sort = he.Select(
        he.Option(he.Str("Par nom"), value="name_asc"),
        he.Option(he.Str("Score croissant"), value="score_asc"),
        he.Option(he.Str("Score décroissant"), value="score_desc"),
        id_="sel_sort_mcq",
        class_="box",
        onchange=(
            "if(typeof renderMcqOverview === 'function') "
            "{ renderMcqOverview(); }"
        )
    )

    chk_group = he.Input(
        type="checkbox",
        id_="chk_group_exo",
        onchange=(
            "if(typeof renderMcqOverview === 'function') "
            "{ renderMcqOverview(); }"
        )
    )
    lbl_group = he.Label(
        chk_group,
        he.Str(" Grouper par exercice"),
        style_="cursor: pointer; user-select: none;"
    )

    card_overview = he.Div(
        he.Div(
            he.H2(
                he.Str("Vue d'ensemble de l'examen"),
                style_="margin: 0; font-size: 1.25rem; color: #1e293b;"
            ),
            he.Div(
                select_overview_exam,
                select_sort,
                lbl_group,
                style_=controls_group_style
            ),
            style_=card_header_style
        ),
        he.Div(
            he.Canvas(
                id_="mcq_overview_chart"),
            style_=chart_container_style
        ),
        style_=card_style
    )

    # card 3: student evolution
    students = ctx.dbs.query(tables.Usr).order_by(
        tables.Usr.usr_name.asc(),
        tables.Usr.usr_fst_name.asc()
    ).all()

    student_options = [
        he.Option(he.Str(lang.txt("stats_select_student")), value="")
    ]
    for std in students:
        student_options.append(
            he.Option(
                he.Str(f"{std.usr_fst_name} {std.usr_name}"),
                value=f"{std.usr_id}"
            )
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
    ).filter(
        tables.Item.itm_usr == current_usr_id
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

    card_evolution = he.Div(
        he.Div(
            he.H2(
                he.Str(lang.txt("stats_evo_title")),
                style_="margin: 0; font-size: 1.25rem; color: #1e293b;"
            ),
            he.Div(
                he.Str("Étudiant : "), select_student,
                he.Str("QCM : "), select_mcq_evo,
                style_=controls_group_style
            ),
            style_=card_header_style
        ),
        he.Div(he.Canvas(id_="evolution_chart"), style_=chart_container_style),
        style_=card_style
    )

    # card 4: tags
    select_tags_sort = he.Select(
        he.Option(he.Str("Du plus dur au plus facile"), value="score_asc"),
        he.Option(he.Str("Du plus facile au plus dur"), value="score_desc"),
        he.Option(he.Str("Par nom (A-Z)"), value="name_asc"),
        id_="sel_sort_tags",
        class_="box",
        onchange="renderTagsOverview()"
    )

    card_tags = he.Div(
        he.Div(
            he.H2(
                he.Str("Analyse par Tags (Compétences)"),
                style_="margin: 0; font-size: 1.25rem; color: #1e293b;"
            ),
            he.Div(
                he.Str("Trier : "), select_tags_sort,
                style_=controls_group_style
            ),
            style_=card_header_style
        ),
        he.Div(
            he.Canvas(id_="tags_overview_chart"),
            style_=chart_container_style
        ),
        style_=card_style
    )

    image_modal = he.Div(
        he.Img(
            id_="modal_image",
            src="",
            style_=(
                "max-width: 90vw; max-height: 90vh; border-radius: 8px; "
                "box-shadow: 0 20px 50px rgba(0,0,0,0.7); object-fit: contain;"
            )
        ),
        id_="image_modal",
        style_=(
            "display: none; position: fixed; top: 0; left: 0; "
            "width: 100vw; height: 100vh; background: rgba(15, 23, 42, 0.80); "
            "backdrop-filter: blur(8px); z-index: 9999; "
            "justify-content: center; align-items: center; cursor: zoom-out;"
        ),
        onclick="this.style.display = 'none';"
    )

    # dashboard
    if exam_id is not None:
        question_element: he.Element = card_question_detail
    else:
        question_element = he.Empty()

    dashboard_root = he.Div(
        header_section,
        question_element,
        card_overview,
        card_evolution,
        card_tags,
        image_modal,
        style_=dashboard_style
    )
    elements.append(dashboard_root)

    return base.page(ctx, "page_title_stats", he.ElementList(*elements))
