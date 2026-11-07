from webamc.www.all import *
from webamc.www.db import util as www_db_util
from webamc.db import queries, tables


def page(ctx: context.Context, args: types.args_oper_t) -> fa.Response:

    exm_id = args["exm_id"]
    exam = queries.get_exam(ctx.dbs, exm_id)
    elements: list[he.Element] = list()
    now = datetime.datetime.now()
    five_min = datetime.timedelta(minutes=5)
    if now < exam.exm_start:
        exam_status: types.exam_status_t = "upcoming"
    elif now > exam.end_time():
        exam_status = "finished"
    else:
        exam_status = "in-progress"


    #####
    # table with user monitoring data
    #####

    # table header
    input_all = he.Input(
        type_="checkbox",
        id_="checkbox_all",
        onclick="exam_select_all_registrations()"
    )
    td_head = [
        he.Td(input_all),
        he.Td(he.Txt("word_usr")),
        he.Td(he.Txt("word_progress")),
        he.Td(he.Txt("word_status"))
    ]
    thead = he.Thead(he.Tr(*td_head))

    # table rows generation
    trs = list()
    no_registered = 0
    for row in queries.get_exam_result(ctx.dbs, exm_id):
        sub: tp.Optional[tables.Submission] = None
        no_registered += 1
        usr_name = row["usr"].fmt()
        tds: list[he.Element] = list()

        if row["sub_result"] is None:
            usr_status: types.exam_usr_status_t = "not-started"
        else:
            sub = row["sub_result"]["sub"]
            assert sub.sub_exm_date_update is not None
            if exam_status == "finished":
                usr_status = "finished"
            elif now - sub.sub_exm_date_update > five_min:
                usr_status = "inactive"
            else:
                usr_status = "online"

        # checkbox using reg_id for deletion actions
        if row["sub_result"] is not None:
            tds.append(he.Empty())
        else:
            reg_id = row["reg"].reg_id
            input_check = he.Input(
                type_="checkbox",
                id_=f"checkbox_{reg_id}",
                class_="checkbox_registration"
            ).set_data(
                "reg_id", str(reg_id)
            )
            tds.append(input_check)

        # usr status
        txt_status = tp.cast(
            types.txt_t,
            f"exam_usr_status_{usr_status.replace('-', '_')}"
        )
        cls_status = f"usr-status-{usr_status}"
        span_status = he.Span(he.Txt(txt_status), class_=cls_status)

        # progress bar
        if row["sub_result"] is None:
            no_questions = 0
            no_answered = 0
        else:
            qst_answers = row["sub_result"]["qst_answers"]
            no_questions = len(qst_answers)
            no_answered = sum(1 for _, c in qst_answers.items() if len(c) > 0)
        progress = he.Progress(
            max_=str(max(1, no_questions)),
            value=str(no_answered)
        )

        # view image
        if sub is None:
            sub_id = None
        else:
            sub_id = sub.sub_id
        img_view = base.static_img(
            "view",
            "exam_view_submission",
            js=f"exam_view_submission({json.dumps(sub_id)})",
            target="_blank"
        )

        tds += [
            he.Str(usr_name),
            progress,
            span_status,
            img_view
        ]
        trs.append(tds)

    if len(trs) == 0:
        table_monitoring: he.Element = he.Empty()
    else:
        table_monitoring = he.mktable(trs, class_="table-solid")
        table_monitoring.insert(0, thead)


    #####
    # table with exam attributes, status, buttons, ...
    #####

    # select with groups to register
    query_grps = queries.get_submit_grps(ctx.dbs, session.usr_id(ctx))
    grps = list(query_grps)
    opts = [
        he.Option(he.Str(grp.grp_name), value=grp.grp_id) for grp in grps
    ]
    select_grp = he.Select(
        *opts,
        id_="grp_id",
        style="vertical-align: middle;"
    ).set_data(
        "type", "integer"
    )
    img_grp_add = base.static_img(
        "group-add",
        "exam_register_group",
        js="exam_register('grp_id')",
        style="vertical-align: middle;"
    )

    # select with users to register
    grps_ids = set(grp.grp_id for grp in grps)
    query_usrs = queries.get_grps_usrs(ctx.dbs, grps_ids, types.USR_RIGHT_VIEW)
    opts = [
        he.Option(he.Str(usr.fmt()), value=usr.usr_id)
        for usr in query_usrs
    ]
    select_usr = he.Select(
        *opts,
        id_="usr_id",
        style="vertical-align: middle;"
    ).set_data(
        "type", "integer"
    )
    img_usr_add = base.static_img(
        "person-add",
        "exam_register_user",
        js="exam_register('usr_id')",
        style="vertical-align: middle;"
    )

    # exam status
    txt_status = tp.cast(
        types.txt_t,
        f"exam_status_{exam_status.replace('-', '_')}"
    )
    span_exam_status = he.Span(
        he.Txt(txt_status),
        class_=f"exam-status-{exam_status}"
    )

    # no of users registered
    str_no_usrs = he.Str(str(no_registered))

    # trs with all previous elements and exam attributes
    uri = base.mkuri(
        "/item/page/main",
        sub_page="item_database",
        itm_id=exam.exm_mcq
    )
    js_mcq_administrate = f"base_new_tab('{uri}')"
    uri = base.mkuri(
        "/mcq/page/form",
        mode="review",
        itm_id=exam.exm_mcq
    )
    js_mcq_view = f"base_new_tab('{uri}')"
    tr_mcq = [
        he.Txt("col_desc_exm_mcq"),
        he.ElementList(
            www_db_util.get_attribute(
                ctx,
                tables.Exam.exm_mcq,
                exam.exm_mcq,
                exam.exm_id,
                updatable=False
            ),
            base.static_img(
                "edit",
                "word_answer",
                js=js_mcq_view,
                style="vertical-align: middle;"
            ),
            base.static_img(
                "settings",
                "word_administrate",
                js=js_mcq_administrate,
                style="vertical-align: middle;"
            )
        )
    ]
    trs = [
        list(e) for e in www_db_util.get_attributes(
            ctx,
            exam,
            tables.Exam.exm_title,
            tables.Exam.exm_start,
            tables.Exam.exm_duration,
            updatable=False
        )
    ] + [
        tr_mcq,
        [
            he.Txt("word_status"),
            span_exam_status
        ],
        [
            he.Txt("exam_select_a_group_to_register"),
            he.ElementList(select_grp, img_grp_add)
        ],
        [
            he.Txt("exam_select_a_user_to_register"),
            he.ElementList(select_usr, img_usr_add)
        ],
        [
            he.Txt("exam_users_registered"),
            str_no_usrs
        ]
    ]

    # tr with buttons
    buttons: list[he.Element] = list()
    btn = base.static_img(
        "trash",
        "exam_delete",
        js=f"exam_delete({exm_id})"
    )
    buttons.append(btn)
    btn = base.static_img(
        "group-delete",
        "exam_delete_selected_registrations",
        js="exam_unregister()"
    )
    buttons.append(btn)
    btn = base.static_img(
        "doc-table",
        "exam_export_scores",
        href=f"../oper/export-scores?exm_id={exm_id}"
    )
    buttons.append(btn)
    trs.append([he.Txt("word_actions"), he.ElementList(*buttons)])

    # assemble the table
    table_exam_status = he.mktable(trs, class_="table-form")

    elements = [
        table_exam_status,
        table_monitoring
    ]

    return fa.responses.HTMLResponse(str(he.ElementList(*elements)))
