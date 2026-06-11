import random

from webamc.www.all import *
from webamc.db import tables, queries


_form_ctx_t = tp.TypedDict(
    "_form_ctx_t",
    {
        "is_root": bool,
        "exe_id": int,
        "qst_id": int,
        "exe_num": int,
        "qst_num": int,
        "content": dict[int, dict[int, list[int]]]
    }
)

_mcq_content_question_t = tp.TypedDict(
    "_mcq_content_question_t",
    {
        "itm_id": int,
        "iti_num": int
    }
)

_mcq_content_exercise_t = tp.TypedDict(
    "_mcq_content_exercise_t",
    {
        "itm_id": int,
        "itm_children": tp.Sequence["_mcq_content_t"]
    }
)

_mcq_content_t = tp.Union[_mcq_content_question_t, _mcq_content_exercise_t]

def page(
        ctx: context.Context,
        mcq_id: int,
        iti_num: int | None = None
) -> fa.Response:

    session.check_logged_in(ctx)

    # get the mcq and the corresponding item
    mcq_item = queries.get_mcq(ctx.dbs, mcq_id)
    if mcq_item is None:
        raise fa.HTTPException(status_code=404)
    mcq, item = mcq_item

    # if an exam registration is active
    active_registration = session.active_registration(ctx)
    exam: tables.Exam | None = None
    registration: tables.Registration | None = None
    if active_registration is None:
        session.check_can_view_mcq(ctx, mcq_id)
    else:
        registration, exam, mcq = active_registration
        if exam.exm_mcq != mcq_id:
            raise fa.HTTPException(status_code=403)

    selected_instance = None
    if iti_num is not None:
        if session.has_admin_right(ctx, item):
            selected_instance = int(iti_num)


    # setup and generate the content
    content, choices = _setup(
        ctx,
        mcq,
        item,
        exam,
        registration,
        selected_instance
    )

    elements: list[he.Element] = list()
    form_ctx: _form_ctx_t = {
        "is_root": True,
        "exe_id": 0,
        "qst_id": 0,
        "exe_num": 0,
        "qst_num": 0,
        "content": dict()
    }
    element_mcq = _form_item(ctx, content, form_ctx)

    # top rule with status boxes
    status_cells: list[he.Element] = list()
    js = ""
    fst = True
    for exe_id, exe_qsts in form_ctx["content"].items():
        if not fst:
            empty_td = he.Td(he.Div(class_="status-box"))
            status_cells += [empty_td, empty_td]
        fst = fst and len(exe_qsts) > 0
        status_cells += [
            he.Td(
                he.Div(
                    id_=f"qst_{qst_id}_status_rule",
                    class_="status-box status-box-question status-unfilled"
                )
            ) for qst_id in exe_qsts
        ]
        js += "\n" + f"mcq_new_exe({exe_id});"
        for qst_id, cho_ids in exe_qsts.items():
            js += "\n" + f"mcq_new_qst({qst_id}, {exe_id})"
            for cho_id in cho_ids:
                js += "\n" + f"mcq_new_cho({cho_id}, {qst_id})"
    if status_cells != list():
        status = he.Div(he.Table(he.Tr(*status_cells)), class_="status-rule")
        elements.append(status)
    js += "\nmcq_init();"

    elements.append(element_mcq)

    # initialise boxes initially checked
    for cho_id in choices:
        js += f"$('#cho_' + {cho_id}).prop('checked', true);"
        js += f"\nmcq_on_choice_click({cho_id});"
        js += f"\nmcq_changes_done = false;"

    # exam mode => initiate the timer
    if exam is not None:
        div_timer = he.Div(
            he.Span(he.Str(""), id_="exam-timer-text"),
            id_="exam-timer"
        )
        d = tables.Exam.end_time(exam)
        js += f"\nvar sec_duration = 60 * {exam.exm_duration};"
        js += f"\nvar end_time = new Date({d.year}, {d.month-1}, {d.day}, "
        js += f"{d.hour}, {d.minute});"
        js += "\nmcq_init_timer(sec_duration, end_time);"
        js += "\nmcq_init_save_timer();"
        elements.append(div_timer)

    # hidden input containing mcq-id
    hidden_id = he.Input(
        id_="mcq_id",
        type_="hidden",
        value=mcq.mcq_id
    )
    elements.append(hidden_id)

    body = he.ElementList(
        *elements,
        he.Script(js)
    )

    # side buttons
    cfg = config.CONFIG
    btns: list[
        tuple[types.static_img_t, types.txt_t, None | tuple[str], str]
    ] = [
        ("arrow-right",
         "param_seq_next_question",
         (cfg["key_qst_next"], ),
         "mcq_move_qst_next()"),
        #
        ("arrow-left",
         "param_seq_previous_question",
         (cfg["key_qst_prev"], ),
         "mcq_move_qst_prev()"),
        #
        ("switch-mode",
         "param_seq_switch_mode",
         (cfg["key_switch_mode"], ),
         "mcq_switch_mode()")
    ]
    if exam is None:
        btns.append(("checkmark", "verb_send", None, "mcq_validate()"))
    else :
        btns.append(("checkmark", "verb_send", None, "mcq_save_answers()"))

    side_buttons = [
        base.static_img(img, title, title_args=title_args, js=js)
        for (img, title, title_args, js) in btns
    ]

    return base.page(ctx, str(item.itm_title), body, side_buttons=side_buttons)


def _gen_mcq_content(
        ctx: context.Context,
        item: tables.Item,
        instance_num: int | None = None
) -> _mcq_content_t:
    def loop(item: tables.Item) -> _mcq_content_t:
        assert item.itm_type != types.ITEM_TYPE_CHOICE

        # question type
        if item.itm_type == types.ITEM_TYPE_QUESTION:
            qsts.add(item.itm_id)

            # getting instance of this question
            instances = queries.get_instances(ctx.dbs, item.itm_id)
            chosen_instance = 1
            if instances:
                if instance_num is not None and \
                    any(i.iti_num == instance_num for i in instances):
                    chosen_instance = instance_num
                else:
                    # choosing random instance
                    chosen_instance = random.choice(instances).iti_num

            # returning tuple with itm id and instance num
            return {"itm_id": item.itm_id, "iti_num": chosen_instance}

        # pack type
        if item.itm_type == types.ITEM_TYPE_PACK:
            packs[item] = list()
            return {"itm_id": item.itm_id, "itm_children": packs[item]}

        # mcq or exercice type
        children = [
            loop(child) for child in queries.get_children(
                ctx.dbs, item.itm_id
            )
        ]
        if item.itm_rnd:
            random.shuffle(children)

        return {"itm_id": item.itm_id, "itm_children": children}

    packs: dict[tables.Item, list[tp.Any]] = dict()
    qsts: set[int] = set()
    result = loop(item)

    # packs
    for item_pack, pack_content in packs.items():
        for item_qst in queries.gen_pack_questions(
                ctx.dbs, item_pack, session.usr_id(ctx), qsts
        ):
            insts = queries.get_instances(ctx.dbs, item_qst.itm_id)
            c_num = 1
            if insts:
                if instance_num is not None and \
                    any(i.iti_num == instance_num for i in insts):
                    c_num = instance_num
                else:
                    c_num = random.choice(insts).iti_num

            pack_content.append({"itm_id": item_qst.itm_id, "iti_num": c_num})
            qsts.add(item_qst.itm_id)

    return result


def _setup(
        ctx: context.Context,
        mcq: tables.Mcq,
        item: tables.Item,
        exam: None | tables.Exam,
        registration: None | tables.Registration,
        instance_num: None | int = None
) -> tuple[_mcq_content_t, list[int]]:

    # in review mode we generate a new content each time the form is
    # reloaded
    if exam is None or registration is None:
        return _gen_mcq_content(ctx, item, instance_num), list()

    # in exam mode we generate the content once and save it in table
    # Submission. then, if the page is reloaded we recover the
    # content. this guarantees that question packs always contain the
    # same questions and that questions/exercices always appear in the
    # same order
    usr_id = session.usr_id(ctx)
    exam_sub = ctx.dbs.query(
        tables.ExamSubmission
    ).where(
        (tables.ExamSubmission.exs_registration == registration.reg_id)
    ).first()
    if exam_sub is not None:
        content = tp.cast(_mcq_content_t, json.loads(exam_sub.exs_content))
        choices = [
            c.cho_id
            for c in queries.get_submission_choices(ctx.dbs, exam_sub.exs_id)
        ]
    else:
        content = _gen_mcq_content(ctx, item, instance_num)
        choices = list()
        sub = tables.Submission(sub_date=datetime.datetime.now())
        ctx.dbs.add(sub)
        ctx.dbs.flush()
        ctx.dbs.refresh(sub)
        exs = tables.ExamSubmission(
            exs_id=sub.sub_id,
            exs_content=json.dumps(content),
            exs_registration=registration.reg_id,
            exs_date_update=datetime.datetime.now()
        )
        ctx.dbs.add(exs)
    result = (content, choices)
    return result


def _form_question(
        ctx: context.Context,
        item: tables.Item,
        iti_num: int | None,       # instance num
        form_ctx: _form_ctx_t
) -> he.Element:
    form_ctx["qst_id"] = item.itm_id
    form_ctx["qst_num"] += 1

    # getting questionf from database
    qst = queries.get_question(ctx.dbs, item.itm_id)

    box_status = he.Div(
        id_=f"qst_{item.itm_id}_status",
        class_="status-box status-box-question status-unfilled"
    )
    lbl = f"Question {form_ctx['qst_num']}"
    if item.itm_title is not None:
        lbl = f"{lbl} - {item.itm_title}"
    lbl_status = he.Span(
        he.Str(lbl),
        id_=f"qst_{item.itm_id}_label",
        class_="question-number"
    )
    tbl_status = he.Table(he.Tr(he.Td(box_status), he.Td(lbl_status)))

    # generate choices
    cho_list = list(queries.get_question_choices(ctx.dbs, item.itm_id))
    form_ctx["content"][form_ctx["exe_id"]][form_ctx["qst_id"]] = [
        int(cho.cho_id) for cho in cho_list
    ]

    if item.itm_rnd:
        cho_list_first = [cho for cho in cho_list if not cho.cho_last]
        cho_list_last = [cho for cho in cho_list if cho.cho_last]
        random.shuffle(cho_list_first)
        random.shuffle(cho_list_last)
        cho_list = cho_list_first + cho_list_last

    tbl_rows: list[he.Tr] = list()
    for cho in cho_list:
        img_file_path = base.img_src(ctx, cho.cho_id, iti_num)

        box_id = f"cho_{cho.cho_id}"
        box_name = f"cho_{item.itm_id}"
        box_type = "checkbox" if qst.qst_type == types.QUESTION_TYPE_MULTI else "radio"

        box = he.Input(
            id_=box_id,
            type_=box_type,
            name=box_name,
            class_="choice-input"
        )
        img = he.Label(
            he.Img(
                src=img_file_path,
                alt=f"cho-{cho.cho_id}"
            ), for_=box_id
        )

        result_box = he.Div(
            id_=f"cho_{cho.cho_id}_status",
            class_="status-box status-box-choice"
        )
        tbl_rows.append(
            he.Tr(
                he.Td(result_box),
                he.Td(box),
                he.Td(img)
            )
        )

    div_body = he.Div(
        he.Img(
            src=base.img_src(
                ctx,
                item.itm_id,
                iti_num
            ),
            alt=f"qst-{item.itm_id}"
        ),
        he.Table(*tbl_rows),
        id_=f"qst_{item.itm_id}_body",
        class_="question-body"
    )

    return he.Div(
        tbl_status,
        div_body,
        id_=f"qst_{item.itm_id}",
        class_="question"
    )


def _form_exercise(
        ctx: context.Context,
        item: tables.Item,
        children: tp.Sequence[_mcq_content_t],
        form_ctx: _form_ctx_t
) -> he.Element:
    form_ctx["exe_id"] = item.itm_id
    form_ctx["content"][item.itm_id] = dict()
    is_root = form_ctx["is_root"]
    form_ctx["is_root"] = False
    if not is_root:
        form_ctx["exe_num"] += 1

    # exercice image
    exercise_elements: list[he.Element] = list()

    # getting instances from db (it's only 1 for an exercice)
    instances = queries.get_instances(ctx.dbs, item.itm_id)

    # image checking
    if instances and instances[0].iti_img is not None:
        first_instance_num = instances[0].iti_num

        img_file_path = base.img_src(
            ctx, item.itm_id,
            first_instance_num
        )
        exercise_elements += [
            he.Img(src=img_file_path, alt=f"exe-{item.itm_id}")
        ]

    # exercise body = html elements of the children
    exercise_elements += [
        _form_item(ctx, child, form_ctx) for child in children
    ]

    # if it is an exercise mcq we just return these elements + the
    # image
    if is_root:
        return he.ElementList(*exercise_elements)

    # if it is a normal exercise we return the title + the image + the
    # children. the image and children are enclosed in a div and the
    # whole is enclosed in another div.
    title = f"Exercice {form_ctx['exe_num']}"
    if item.itm_title is not None:
        title = title + " - " + html.escape(item.itm_title)
    span_title = he.Span(
        he.Str(title),
        id_=f"exe_{item.itm_id}_label",
        class_="exercise-title"
    )
    div_body = he.Div(
        *exercise_elements,
        id_=f"exe_{item.itm_id}_body",
        class_="exercise-body"
    )
    result = he.Div(
        span_title,
        div_body,
        id_=f"exe_{item.itm_id}",
        class_="exercise"
    )
    return result


def _form_item(
        ctx: context.Context,
        content: _mcq_content_t,
        form_ctx: _form_ctx_t
) -> he.Element:
    # if it's a dict with iti_num, new question struct
    if isinstance(content, dict) and "iti_num" in content:
        qst_content = tp.cast(_mcq_content_question_t, content)
        return _form_question(
            ctx,
            queries.get_item(ctx.dbs, qst_content["itm_id"]),
            qst_content["iti_num"],
            form_ctx
        )
    # if it's an exercice or a pack
    else:
        return _form_exercise(
            ctx,
            queries.get_item(ctx.dbs, content["itm_id"]),
            content["itm_children"],
            form_ctx
        )
