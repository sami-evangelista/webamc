import random

from webamc.www.all import *
from webamc.db import tables, queries


class form_ctx_t(tp_ext.TypedDict):
    mode: types.mcq_form_mode_t
    is_root: bool
    exe_id: int
    qst_id: int
    exe_num: int
    qst_num: int
    content: dict[int, dict[int, list[int]]]
    sub_result: None | queries.submission_result_t


def page(
        ctx: context.Context,
        mode: types.mcq_form_mode_t,
        itm_id: int | None,
        sub_id: int | None
) -> fa.Response:

    session.check_logged_in(ctx)
    item: tables.Item
    exam: tables.Exam | None = None
    reg: tables.Registration | None = None

    # check parameters and rights
    if mode == "review":
        if itm_id is None:
            raise fa.HTTPException(status_code=422)
        session.check_can_view_mcq(ctx, itm_id)
    elif mode == "exam":
        active_reg = session.active_registration(ctx)
        if active_reg is None:
            raise fa.HTTPException(status_code=422)
        reg, exam = active_reg
        itm_id = exam.exm_mcq
    elif mode == "view":
        def owns(itm_id: int) -> bool:
            owner = queries.get_item_owner(ctx.dbs, itm_id)
            return owner is not None and owner.usr_id == usr_id
        if sub_id is None:
            raise fa.HTTPException(status_code=422)
        usr_id = session.usr_id(ctx)
        sub, reg, exam = queries.get_submission(ctx.dbs, sub_id)
        if not (
                sub.sub_rev_usr == usr_id
                or (reg is not None and reg.reg_usr == usr_id)
                or (sub.sub_rev_mcq is not None and owns(sub.sub_rev_mcq))
                or (exam is not None and owns(exam.exm_mcq))
        ):
            raise fa.HTTPException(status_code=403)
        if sub.sub_rev_mcq is not None:
            itm_id = sub.sub_rev_mcq
        elif exam is not None:
            itm_id = exam.exm_mcq
        else:
            assert False
    else:
        assert False

    # get item
    item = queries.get_item(ctx.dbs, itm_id)

    # setup and generate the content
    content, choices = _setup(ctx, mode, item, exam, reg)

    # in view mode get submission result
    if mode != "view":
        subres = None
    else:
        if sub_id is None:
            raise fa.HTTPException(status_code=422)
        subres = queries.get_submission_result(ctx.dbs, sub_id)
        choices = list(
            cho.itm_id
            for qst, qst_choices in subres["qst_answers"].items()
            for cho in qst_choices
        )

    elements: list[he.Element] = list()
    form_ctx: form_ctx_t = {
        "mode": mode,
        "sub_result": subres,
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
        fst = fst and len(exe_qsts) == 0
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
    js += f"\nmcq_init({json.dumps(content)});"

    elements.append(element_mcq)

    # initialise boxes initially checked
    for cho_id in choices:
        js += f"\n$('#cho_' + {cho_id}).prop('checked', true);"
        if subres is None:
            js += f"\nmcq_on_choice_click({cho_id});"
    js += "\nmcq_changes_done = false;"

    # exam mode => initiate the timer
    if mode == "exam":
        assert exam is not None
        div_timer = he.Div(
            he.Span(he.Str(""), id_="exam-timer-text"),
            id_="exam-timer"
        )
        d = exam.end_time()
        js += f"\nvar sec_duration = 60 * {exam.exm_duration};"
        js += f"\nvar end_time = new Date({d.year}, {d.month - 1}, {d.day}, "
        js += f"{d.hour}, {d.minute});"
        js += "\nmcq_init_timer(sec_duration, end_time);"
        js += "\nmcq_init_save_timer();"
        elements.append(div_timer)

    # hidden input containing mcq-id
    hidden_id = he.Input(
        id_="itm_id",
        type_="hidden",
        value=item.itm_id
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
    ] = list()
    if mode == "view":
        side_buttons = None
    else:
        btns += [
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
        if mode != "exam":
            btns += [
                ("arrow-clockwise", "word_restart", None, "mcq_reset_all()"),
                ("checkmark", "word_send", None, "mcq_validate()")
            ]
        else:
            btns += [
                ("save", "word_send", None, "mcq_save_exam()")
            ]
        side_buttons = [
            base.static_img(img, title, title_args=title_args, js=js)
            for (img, title, title_args, js) in btns
        ]

    # title
    if mode != "exam":
        title = item.itm_title
    else:
        assert exam is not None
        title = exam.exm_title

    return base.page(
        ctx,
        "mcq",
        body,
        title=title,
        side_buttons=side_buttons,
        show_menu=reg is None
    )


def _gen_mcq_content(
        ctx: context.Context,
        item: tables.Item
) -> types.mcq_content_t:
    def loop(item: tables.Item) -> types.mcq_content_t:

        assert item.itm_type != types.ITEM_TYPE_CHOICE
        result: types.mcq_content_t

        # get an instance of this item
        instances = queries.get_instances(ctx.dbs, item.itm_id)
        assert len(instances) > 0
        inst = random.choice(instances)

        # question type
        if item.itm_type == types.ITEM_TYPE_QUESTION:
            qsts.add(item.itm_id)
            result = {
                "itm_id": item.itm_id,
                "itm_type": types.ITEM_TYPE_QUESTION,
                "itm_qst_type": item.itm_qst_type,
                "iti_id": inst.iti_id,
                "iti_num": inst.iti_num,
                "children": None
            }

        # pack type
        elif item.itm_type == types.ITEM_TYPE_PACK:
            packs[item] = list()
            result = {
                "itm_id": item.itm_id,
                "itm_type": types.ITEM_TYPE_PACK,
                "itm_qst_type": item.itm_qst_type,
                "iti_id": inst.iti_id,
                "iti_num": inst.iti_num,
                "children": packs[item]
            }

        # mcq or exercise type
        else:
            children = [
                loop(child) for child in queries.get_children(
                    ctx.dbs, item.itm_id
                )
            ]
            if item.itm_rnd:
                random.shuffle(children)
            result = {
                "itm_id": item.itm_id,
                "itm_type": types.ITEM_TYPE_EXERCISE,
                "itm_qst_type": item.itm_qst_type,
                "iti_id": inst.iti_id,
                "iti_num": inst.iti_num,
                "children": children
            }

        return result

    packs: dict[tables.Item, list[types.mcq_content_t]] = dict()
    qsts: set[int] = set()
    result = loop(item)

    # packs
    for item_pack, pack_content in packs.items():
        for item_qst in queries.gen_pack_questions(
                ctx.dbs, item_pack, session.usr_id(ctx), qsts
        ):
            instances = queries.get_instances(ctx.dbs, item_qst.itm_id)
            assert len(instances) > 0
            inst = random.choice(instances)

            pack_content.append({
                "itm_id": item_qst.itm_id,
                "itm_type": types.ITEM_TYPE_QUESTION,
                "itm_qst_type": item.itm_qst_type,
                "iti_num": inst.iti_num,
                "iti_id": inst.iti_id,
                "children": None
            })
            qsts.add(item_qst.itm_id)

    return result


def _setup(
        ctx: context.Context,
        mode: types.mcq_form_mode_t,
        item: tables.Item,
        exam: None | tables.Exam,
        reg: None | tables.Registration
) -> tuple[types.mcq_content_t, list[int]]:

    # in a non exam mode we generate a new content each time the form
    # is reloaded
    if mode != "exam":
        return _gen_mcq_content(ctx, item), list()

    # in exam mode we generate the content once and save it in table
    # Submission. then, if the page is reloaded we recover the
    # content. this guarantees that question packs always contain the
    # same questions and that questions/exercices always appear in the
    # same order
    assert reg is not None
    sub = queries.get_registration_submission(ctx.dbs, reg)
    if sub is not None:
        content = tp.cast(types.mcq_content_t, json.loads(sub.sub_content))
        choices = [
            c.itm_id for c in queries.get_submission_choices(ctx.dbs, sub)
        ]
    else:
        content = _gen_mcq_content(ctx, item)
        choices = list()
        exs = tables.Submission(
            sub_type=types.SUBMISSION_TYPE_EXAM,
            sub_date=datetime.datetime.now(),
            sub_content=json.dumps(content),
            sub_exm_registration=reg.reg_id,
            sub_exm_date_update=datetime.datetime.now()
        )
        ctx.dbs.add(exs)
    result = (content, choices)
    return result


def _form_question(
        ctx: context.Context,
        item: tables.Item,
        iti_num: int,
        form_ctx: form_ctx_t
) -> he.Element:

    form_ctx["qst_id"] = item.itm_id
    form_ctx["qst_num"] += 1

    # question label and status
    box_status = he.Div(
        id_=f"qst_{item.itm_id}_status",
        class_="status-box status-box-question"
    )
    subres = form_ctx["sub_result"]
    if subres is None or len(subres["qst_answers"][item]) == 0:
        status = "unfilled"
    elif subres["qst_score"][item] <= 0:
        status = "wrong"
    elif subres["qst_score"][item] == subres["qst_max_score"][item]:
        status = "correct"
    else:
        status = "partially-correct"
    js = f"mcq_set_qst_status({item.itm_id}, '{status}')"
    lbl = lang.txt("word_question").title() + " " + str(form_ctx["qst_num"])
    if item.itm_title is not None:
        lbl = f"{lbl} - {item.itm_title}"
    lbl_status = he.Span(
        he.Str(lbl),
        id_=f"qst_{item.itm_id}_label",
        class_="question-number"
    )
    tbl_status = he.mktable([[box_status, lbl_status]])

    # generate choices
    cho_list = list(queries.get_children(ctx.dbs, item.itm_id))
    form_ctx["content"][form_ctx["exe_id"]][form_ctx["qst_id"]] = [
        int(cho.itm_id) for cho in cho_list
    ]
    if item.itm_rnd:
        cho_list_first = [cho for cho in cho_list if not cho.itm_cho_last]
        cho_list_last = [cho for cho in cho_list if cho.itm_cho_last]
        random.shuffle(cho_list_first)
        random.shuffle(cho_list_last)
        cho_list = cho_list_first + cho_list_last

    trs: list[list[he.Element]] = list()
    for cho in cho_list:
        iti = queries.get_item_instance(ctx.dbs, cho.itm_id, iti_num)
        if iti is None:
            continue
        img: he.Element = he.Img(
            src=base.img_src(ctx, iti.iti_id, iti.iti_uuid),
            alt=f"cho-{cho.itm_id}"
        )

        box_id = f"cho_{cho.itm_id}"
        box_name = f"cho_{item.itm_id}"
        if item.itm_qst_type == types.QUESTION_TYPE_MULTI:
            box_type = "checkbox"
        else:
            box_type = "radio"

        box = he.Input(
            id_=box_id,
            type_=box_type,
            name=box_name,
            class_="choice-input"
        ).add_flag(
            "disabled", subres is not None
        )
        label = he.Label(img, for_=box_id)
        result_box = he.Div(
            id_=f"cho_{cho.itm_id}_status",
            class_="status-box status-box-choice"
        )
        if subres is not None:
            if subres["cho_correct"].get(cho, not cho.itm_cho_correct):
                js += f"\nmcq_set_cho_status({cho.itm_id}, 'correct')"
            else:
                js += f"\nmcq_set_cho_status({cho.itm_id}, 'wrong')"
        trs.append([result_box, box, label])

    iti = queries.get_item_instance(ctx.dbs, item.itm_id, iti_num)
    if iti is None:
        img = he.Empty()
    else:
        img = he.Img(
            src=base.img_src(ctx, iti.iti_id, iti.iti_uuid),
            alt=f"qst-{item.itm_id}"
        )
    div_body = he.Div(
        img,
        he.mktable(trs),
        he.Script(js),
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
        children: tp.Sequence[types.mcq_content_t],
        form_ctx: form_ctx_t
) -> he.Element:
    form_ctx["exe_id"] = item.itm_id
    form_ctx["content"][item.itm_id] = dict()
    is_root = form_ctx["is_root"]
    form_ctx["is_root"] = False
    if not is_root:
        form_ctx["exe_num"] += 1

    # exercice image
    exercise_elements: list[he.Element] = list()

    # getting instances from db
    instances = queries.get_instances(ctx.dbs, item.itm_id)

    # image checking
    if instances and instances[0].iti_img is not None:
        img_file_path = base.img_src(
            ctx,
            instances[0].iti_id,
            instances[0].iti_uuid
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
    title = lang.txt("word_exercise").title() + " " + str(form_ctx["exe_num"])
    if item.itm_title is not None:
        title = title + " - " + item.itm_title
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
        content: types.mcq_content_t,
        form_ctx: form_ctx_t
) -> he.Element:

    # it's a question
    if content["itm_type"] == types.ITEM_TYPE_QUESTION:
        return _form_question(
            ctx,
            queries.get_item(ctx.dbs, content["itm_id"]),
            content["iti_num"],
            form_ctx
        )

    # otherwise it's an exercice or a pack
    assert content["children"] is not None
    return _form_exercise(
        ctx,
        queries.get_item(ctx.dbs, content["itm_id"]),
        content["children"],
        form_ctx
    )
