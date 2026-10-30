from webamc.www.all import *
from webamc.db import queries
from webamc.util import fmt


def page(ctx: context.Context, args: types.args_oper_t) -> fa.Response:

    exm_id = args["exm_id"]
    monitoring_data = queries.get_exam_monitoring(ctx.dbs, exm_id)
    if not monitoring_data:
        return fa.responses.HTMLResponse(lang.txt("err_exam_not_found"))

    #####
    # first table with exam attributes, status, buttons, ...
    #####

    # select with groups to register
    query_grps = queries.get_submit_grps(ctx.dbs, session.usr_id(ctx))
    grps = list(query_grps)
    opts = [
        he.Option(he.Str(grp.grp_name), value=grp.grp_id) for grp in grps
    ]
    select_grp = he.Select(
        he.Option(he.Str("-"), value=""),
        *opts,
        id_="grp_id",
        onchange="exam_register()"
    ).set_data(
        "type", "integer"
    )

    # select with users to register
    grps_ids = set(grp.grp_id for grp in grps)
    query_usrs = queries.get_grps_usrs(ctx.dbs, grps_ids, types.USR_RIGHT_VIEW)
    opts = [
        he.Option(
            he.Str(fmt.fmt_name(usr.usr_fst_name, usr.usr_name, False)),
            value=usr.usr_id
        )
        for usr in query_usrs
    ]
    select_usr = he.Select(
        he.Option(he.Str("-"), value=""),
        *opts,
        id_="usr_id",
        onchange="exam_register()"
    ).set_data(
        "type", "integer"
    )

    # exam status
    exam_status: types.exam_status_t = monitoring_data.get(
        "status", "upcoming"
    )
    exam_not_started = exam_status == "upcoming"
    exam_finished = exam_status == "finished"
    txt_status = tp.cast(
        types.txt_t,
        f"seq_exam_status_{exam_status.replace('-', '_')}"
    )
    span_exam_status = he.Span(
        he.Txt(txt_status),
        class_=f"exam-status-{exam_status}"
    )

    # no of users registered
    str_no_usrs = he.Str(str(len(monitoring_data["students"])))

    # trs with all previous elements
    trs_exam_status: list[list[he.Element]] = [
        [he.Txt("seq_exam_status"), span_exam_status],
        [he.Txt("seq_select_a_group_to_register"), select_grp],
        [he.Txt("seq_select_a_user_to_register"), select_usr],
        [he.Txt("seq_users_registered"), str_no_usrs]
    ]

    # tr with buttons
    buttons: list[he.Element] = list()
    if exam_not_started and len(monitoring_data["students"]) > 0:
        btn = base.static_img(
            "trash",
            "seq_delete_selected_registrations",
            js="exam_delete_registrations()"
        )
        buttons.append(btn)
    if exam_finished:
        btn = base.static_img(
            "doc-table",
            "seq_export_exam_scores",
            href=f"../oper/export-scores?exm_id={exm_id}"
        )
        buttons.append(btn)
    if buttons != list():
        trs_exam_status.append([he.ElementList(*buttons), he.Empty()])

    # assemble the table
    table_exam_status = he.mktable(trs_exam_status, class_="table-form")

    #####
    # second table with user monitoring data
    #####

    # table header
    td_head = [
        he.Td(he.Txt("word_student")),
        he.Td(he.Txt("word_progress")),
        he.Td(he.Txt("word_status"))
    ]
    if exam_not_started:
        input_all = he.Input(
            type_="checkbox",
            id_="checkbox_all",
            onclick="exam_select_all_registrations()"
        )
        td_head.insert(0, he.Td(input_all))
    thead = he.Thead(he.Tr(*td_head))

    # table rows generation
    trs: list[list[he.Element]] = list()
    for student in monitoring_data["students"]:
        student_name = fmt.fmt_name(
            student["usr_fst_name"],
            student["usr_name"],
            False
        )
        status = student["status"]
        tds = []

        # checkbox using reg_id for deletion actions
        if exam_not_started:
            input_check = he.Input(
                type_="checkbox",
                id_=f"checkbox_{student['reg_id']}",
                class_="checkbox_registration"
            ).set_data(
                "reg_id", str(student['reg_id'])
            )
            tds.append(input_check)

        # student status
        txt_status = tp.cast(
            types.txt_t,
            f"seq_exam_student_status_{status.replace('-', '_')}"
        )
        cls_status = f"student-status-{student['status']}"
        span_status = he.Span(he.Txt(txt_status), class_=cls_status)

        # progress bar logic
        answered = student["answered_count"]
        total_questions = student["total_questions"]
        progress = he.Progress(
            max_=str(max(1, total_questions)),
            value=str(answered)
        )

        tds += [
            he.Str(student_name),
            progress,
            span_status
        ]
        trs.append(tds)

    # assemble page elements
    elements: list[he.Element] = list()
    elements.append(table_exam_status)

    # data table
    if len(monitoring_data["students"]) > 0:
        table_monitoring = he.mktable(trs, class_="table-solid")
        table_monitoring.insert(0, thead)
        elements.append(table_monitoring)

    return fa.responses.HTMLResponse(str(he.ElementList(*elements)))
