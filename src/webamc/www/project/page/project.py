import json

from webamc.www.all import *
from webamc.www.project import util
from webamc.www.db import util as www_db_util
from webamc.db import queries, tables
from webamc import project as proj


def page(ctx: context.Context, args: types.args_oper_t) -> fa.Response:

    prj = util.get_project(ctx, args["prj_id"])
    trs: list[tuple[he.Element, he.Element, he.Element]] = list()

    def file_elements(f: types.file_t) -> tuple[he.Element, he.Element]:
        span = he.Span(
            he.Txt(proj.file_txt(f), fmt=False),
            id_=f"label-file-{f}"
        )
        file_img = he.Img(
            src=base.static_img_src(base.file_img(proj.file_name(f))),
            title=f,
            alt=f,
            id_=f"img-file-{f}"
        )
        return file_img, span

    def list_action_files(action: types.action_t) -> None:
        trs_files = [
            he.Tr(*[he.Td(e) for e in file_elements(f)])
            for f in proj.list_action_files(action)
        ]
        if trs_files != list():
            table = he.Table(*trs_files)
            trs.append((he.Empty(), table, he.Empty()))

    def label_action(
            action: types.action_t,
            txt: types.txt_t,
            help_section: str | None
    ) -> he.Element:
        result = he.Span(
            he.Txt(txt),
            id_=f"label-action-{action}"
        )
        if help_section is not None:
            base.mkhelp(result, "project", section=help_section)
        return result

    def new_action(
            action: types.action_t,
            txt: types.txt_t,
            js: None | str = None,
            icon: types.static_img_t = "play",
            img_txt: types.txt_t = "base_start",
            help_section: str | None = None
    ) -> None:
        if js is None:
            js = f"project_action('{action}');"
        a = base.static_img(
            icon,
            img_txt,
            js=js,
            id_=f"img-action-{action}"
        )
        trs.append((a, label_action(action, txt, help_section), he.Empty()))
        list_action_files(action)

    def new_upload_action(
            action: types.action_t,
            f: types.file_t,
            txt: types.txt_t,
            help_section: None | str = None
    ) -> None:
        input_file = he.Input(
            type_="file",
            id_=f,
            name=f
        )
        a = base.static_img(
            "upload",
            "base_send",
            js=f"project_upload_action('{action}', '{f}')",
            id_=f"img-action-{action}"
        )
        trs.append((a, label_action(action, txt, help_section), input_file))
        list_action_files(action)

    # div with actions
    new_upload_action(
        "upload_source",
        "source",
        "project_upload_latex_archive",
        help_section="help-project-action-upload"
    )
    new_action(
        "compile",
        "project_compile_latex"
    )
    new_upload_action(
        "upload_answer_sheets",
        "pdf_answer_sheets",
        "project_upload_answer_sheets"
    )
    new_action(
        "analyse",
        "project_analyse_answer_sheets"
    )
    new_action(
        "associate_automatic",
        "project_associate_automatic"
    )
    new_action(
        "associate_manual_prepare",
        "project_associate_manual",
        js="project_manual_association_open()"
    )
    new_action(
        "export_scores",
        "project_generate_scores_and_annotated_sheets"
    )
    new_action(
        "send_annotated_sheets",
        "project_send_annotated_sheets"
    )
    new_action(
        "send_notification_mail",
        "project_send_notification_mail"
    )
    new_action(
        "delete",
        "project_delete",
        icon="trash",
        img_txt="base_delete"
    )
    img, span = file_elements("log_webamc")
    tr = he.Tr(
        he.Td(img),
        he.Td(span),
        he.Td()
    )
    trs.append((img, span, he.Empty()))
    table_actions = he.mktable(
        trs,
        class_="table-form",
        id_="table-action"
    )
    div_actions = he.Div(
        he.H2(he.Txt("base_actions")),
        table_actions
    )

    # div with data
    cols = [
        tables.Project.prj_title,
        tables.Project.prj_copies,
        tables.Project.prj_threshold,
        tables.Project.prj_amc_code,
        tables.Project.prj_auto_assoc_attr
    ]
    trs_data = [
        (label, inpt)
        for label, inpt in www_db_util.get_attributes(ctx, prj, *cols)
    ]
    trs_data.append(
        (he.Txt("base_groups"), he.Div(id_="div-grps"))
    )

    table_data = he.mktable(
        trs_data,
        class_="table-form"
    )
    span_parameters = base.mkhelp(
        he.Span(he.Txt("base_parameters")),
        "project",
        section="help-project-parameters"
    )
    div_data = he.Div(
        he.H2(span_parameters),
        table_data,
        style="position: relative;"
    )

    # div manual association
    div_manual_assoc = he.Div(
        id_="div-manual-association"
    )

    div_left = he.Div(
        div_actions,
        style="min-width: 400px;"
    )
    div_separator = he.Div(
        style="width: 50px;"
    )
    div_right = he.Div(
        div_manual_assoc,
        div_data,
        id_="div-right",
        style="min-width: 400px; position: relative;"
    )

    div_main = he.Div(
        div_left,
        div_separator,
        div_right,
        style="display: flex;"
    )

    grps = {
        grp.grp_id: grp.grp_name
        for grp in queries.get_submit_grps(ctx.dbs, session.usr_id(ctx))
    }
    prj_grps = [
        g.grp_id
        for g in queries.list_project_groups(ctx.dbs, prj.prj_id)
    ]
    script_init = he.Script(
        "project_manual_association_close();"
        f"\nnew GrpTable('div-grps', {json.dumps(grps)},"
        f" {json.dumps(prj_grps)}, true, project_add_group,"
        " true, project_del_group);"
        "\nproject_init();"
    )

    elements = he.ElementList(div_main, script_init)

    return fa.responses.HTMLResponse(str(elements))
