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
    sub: tables.Submission | None = None
    subres: queries.submission_result_t | None = None
    sub_usr_id: int | None = None


    ###
    # check parameters and rights
    ###

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
        sub_reg_exam = queries.get_submission(ctx.dbs, sub_id)
        if sub_reg_exam is None:
            raise fa.HTTPException(status_code=422)
        sub, reg, exam = sub_reg_exam
        if not (
                # review submission made by the user
                (sub.sub_rev_usr == usr_id
                 and sub.sub_visible)
                or
                # exam submission made by the user
                (reg is not None
                 and sub.sub_visible
                 and reg.reg_usr == usr_id)
                or
                # review submission made for an mcq owned by the user
                (sub.sub_rev_mcq is not None
                 and owns(sub.sub_rev_mcq))
                or
                # exam submission made for an exam owned by the user
                (exam is not None
                 and owns(exam.exm_mcq))
        ):
            raise fa.HTTPException(status_code=403)
        if sub.sub_type == types.SUBMISSION_TYPE_REVIEW:
            assert sub.sub_rev_mcq is not None
            assert sub.sub_rev_usr is not None
            itm_id = sub.sub_rev_mcq
            sub_usr_id = sub.sub_rev_usr
        elif sub.sub_type == types.SUBMISSION_TYPE_EXAM:
            assert exam is not None
            assert reg is not None
            itm_id = exam.exm_mcq
            sub_usr_id = reg.reg_usr
        else:
            assert False
    else:
        assert False

    # get item
    item = queries.get_item(ctx.dbs, itm_id)


    ###
    # compute form content and choices initially checked
    ###

    # in review mode we generate a new content. no choices checked
    if mode == "review":
        content = _gen_mcq_content(ctx, item)
        choices = list()

    # in view mode we get content and choices from the submission
    elif mode == "view":
        assert sub_id is not None
        assert sub is not None
        subres = queries.get_submission_result(ctx.dbs, sub_id)
        choices = list(
            cho.itm_id
            for qst, qst_choices in subres["qst_answers"].items()
            for cho in qst_choices
        )
        content = types.check_mcq_content(sub.sub_content)

    # in exam mode we generate the content once and save it in table
    # Submission. then, if the page is reloaded we recover the
    # content. this guarantees that question packs always contain the
    # same questions and that questions/exercices always appear in the
    # same order
    elif mode == "exam":
        assert reg is not None
        sub = queries.get_registration_submission(ctx.dbs, reg)
        if sub is not None:
            content = types.check_mcq_content(sub.sub_content)
            choices = [
                c.itm_id for c in queries.get_submission_choices(ctx.dbs, sub)
            ]
        else:
            content = _gen_mcq_content(ctx, item)
            choices = list()
            now = datetime.datetime.now()
            exs = tables.Submission(
                sub_type=types.SUBMISSION_TYPE_EXAM,
                sub_date=now,
                sub_date_update=now,
                sub_visible=False,
                sub_content=json.dumps(content),
                sub_exm_registration=reg.reg_id
            )
            ctx.dbs.add(exs)
    else:
        raise fa.HTTPException(status_code=422)


    ###
    # now we can generate elements of the page
    ###

    body: list[he.Element] = list()
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
    tds: list[he.Element] = list()
    js = ""
    fst = True
    for exe_id, exe_qsts in form_ctx["content"].items():
        if not fst:
            empty_td = he.Div(class_="mcq-status-box")
            tds += [empty_td, empty_td]
        fst = fst and len(exe_qsts) == 0
        tds += [
            he.Div(
                id_=f"qst_{qst_id}_status_rule",
                class_=(
                    "mcq-status-box mcq-status-box-question "
                    "mcq-status-unfilled"
                )
            ) for qst_id in exe_qsts
        ]
        js += "\n" + f"mcq_new_exe({exe_id});"
        for qst_id, cho_ids in exe_qsts.items():
            js += "\n" + f"mcq_new_qst({qst_id}, {exe_id})"
            for cho_id in cho_ids:
                js += "\n" + f"mcq_new_cho({cho_id}, {qst_id})"
    if len(tds) > 0:
        status = he.Div(
            he.mktable([tds]),
            class_="mcq-status-rule"
        )
        body.append(status)
    if mode == "view":
        init_mode = "mcq_mode_all"
    else:
        init_mode = "mcq_mode_one_by_one"
    js += f"\nmcq_init({init_mode}, {json.dumps(content)});"

    body.append(element_mcq)

    # initialise boxes initially checked
    for cho_id in choices:
        js += f"\n$('#cho_' + {cho_id}).prop('checked', true);"
        if subres is None:
            js += f"\nmcq_on_choice_click({cho_id});"
    js += "\nmcq_changes_done = false;"

    # exam mode => initiate the timer
    if mode == "exam":
        assert exam is not None
        d = exam.end_time()
        js += f"\nvar sec_duration = 60 * {exam.exm_duration};"
        js += f"\nvar end_time = new Date({d.year}, {d.month - 1}, {d.day}, "
        js += f"{d.hour}, {d.minute});"
        js += "\nmcq_init_timer(sec_duration, end_time);"
        js += "\nmcq_init_save_timer();"
        div_timer = he.Div(
            he.Span(he.Str(""), id_="mcq-exam-timer-text"),
            id_="mcq-exam-timer"
        )
        body.append(div_timer)

    # view mode => create the div containing total score and user name
    #   if the user that made the submission is not the connected user
    if mode == "view":
        assert subres is not None
        assert sub_usr_id is not None
        total_score_elements: list[he.Element] = list()
        if sub_usr_id != usr_id:
            usr = queries.get_usr(ctx.dbs, sub_usr_id)
            assert usr is not None
            total_score_elements = [
                he.Str(usr.fmt()), he.nbsp, he.Str("-"), he.nbsp
            ]
        txt = he.Txt(
            "mcq_param_total_score",
            str(subres["score"][item]) + " / " + str(subres["max_score"][item])
        )
        total_score_elements.append(txt)
        div_total_score = he.Div(
            *total_score_elements,
            class_="mcq-total-score-box"
        )
        body.append(div_total_score)

    # hidden input containing mcq-id
    hidden_id = he.Input(
        id_="itm_id",
        type_="hidden",
        value=item.itm_id
    )
    body.append(hidden_id)

    # side buttons
    cfg = config.CONFIG
    btns: list[
        tuple[types.static_img_t, types.txt_t, None | tuple[str], str]
    ] = list()
    btns += [
        ("arrow-right",
         "mcq_param_next_question",
         (cfg["key_qst_next"], ),
         "mcq_move_qst_next()"),
        #
        ("arrow-left",
         "mcq_param_prev_question",
         (cfg["key_qst_prev"], ),
         "mcq_move_qst_prev()"),
        #
        ("switch-mode",
         "mcq_param_switch_mode",
         (cfg["key_switch_mode"], ),
         "mcq_switch_mode()")
    ]
    if mode == "exam":
        btns += [
            ("save", "base_send", None, "mcq_save_exam()")
        ]
    elif mode == "review":
        btns += [
            ("arrow-clockwise", "base_restart", None, "mcq_reset_all()"),
            ("checkmark", "base_send", None, "mcq_save_review()")
        ]
    side_buttons = [
        base.static_img(img, title, title_args=title_args, js=js)
        for (img, title, title_args, js) in btns
    ]

    # title
    if exam is None:
        title = item.itm_title
    else:
        title = exam.exm_title

    show_menu = mode != "exam"
    return base.page(
        ctx,
        "mcq",
        he.ElementList(*body, he.Script(js)),
        title=title,
        side_buttons=side_buttons,
        show_menu=show_menu
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
        class_="mcq-status-box mcq-status-box-question"
    )
    subres = form_ctx["sub_result"]
    if subres is None or len(subres["qst_answers"][item]) == 0:
        status = "unfilled"
    elif subres["score"][item] <= 0:
        status = "wrong"
    elif subres["score"][item] == subres["max_score"][item]:
        status = "correct"
    else:
        status = "partially-correct"
    js = f"mcq_set_qst_status({item.itm_id}, '{status}')"
    title = lang.txt("base_question").title() + " " + str(form_ctx["qst_num"])
    if item.itm_title is not None:
        title = f"{title} - {item.itm_title}"
    span_status = he.Span(
        he.Str(title),
        id_=f"qst_{item.itm_id}_label",
        class_="mcq-question-number"
    )
    tds = [
        he.Td(box_status, style="vertical-align: middle"),
        he.Td(span_status, style="vertical-align: middle")
    ]
    if subres is not None:
        score = (
            str(subres["score"][item])
            + " / " + str(subres["max_score"][item])
        )
        span_score = he.Span(he.Str(score), class_="mcq-score-box")
        tds.append(
            he.Td(he.nbsp, span_score, style="vertical-align: middle")
        )
    tbl_status = he.Table(he.Tr(*tds))

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
            "disabled", form_ctx["mode"]=="view"
        )
        label = he.Label(img, for_=box_id)
        result_box = he.Div(
            id_=f"cho_{cho.itm_id}_status",
            class_="mcq-status-box mcq-status-box-choice"
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
        class_="mcq-question-body"
    )

    return he.Div(
        tbl_status,
        div_body,
        id_=f"qst_{item.itm_id}",
        class_="mcq-question"
    )


def _form_exercise(
        ctx: context.Context,
        item: tables.Item,
        children: tp.Sequence[types.mcq_content_t],
        form_ctx: form_ctx_t
) -> he.Element:

    subres = form_ctx["sub_result"]
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
    title = lang.txt("base_exercise").title() + " " + str(form_ctx["exe_num"])
    if item.itm_title is not None:
        title = title + " - " + item.itm_title
    span_title = he.Span(
        he.Str(title),
        id_=f"exe_{item.itm_id}_label",
        class_="mcq-exercise-title"
    )
    if subres is None:
        element_title: he.Element = span_title
    else:
        score = (
            str(subres["score"][item])
            + " / " + str(subres["max_score"][item])
        )
        span_score = he.Span(he.Str(score), class_="mcq-score-box")
        element_title = he.Table(
            he.Tr(
                he.Td(span_title, style="valign: middle"),
                he.Td(he.nbsp, span_score, style="valign: middle")
            )
        )
    div_body = he.Div(
        *exercise_elements,
        id_=f"exe_{item.itm_id}_body",
        class_="mcq-exercise-body"
    )
    result = he.Div(
        element_title,
        div_body,
        id_=f"exe_{item.itm_id}",
        class_="mcq-exercise"
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
