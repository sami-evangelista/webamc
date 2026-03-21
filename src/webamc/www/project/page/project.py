#!/usr/bin/env python3

import json

from webamc.www.all import *
from webamc.www.project import router
from webamc.util import fmt, io
from webamc.db import queries, tables
from webamc import project as proj


def page(
        ctx: context.Context,
        args: router.args_project_code_t
) -> fa.Response:
    trs: list[he.Element] = list()

    def list_files(
            action: proj.action_t
    ) -> None:
        trs_files = list()
        for f in proj.list_files(action):
            ext = io.get_file_extension(f)
            try:
                doc_types: dict[str, types.static_img_t] = {
                    ".pdf": "doc-pdf",
                    ".ods": "doc-table",
                    ".zip": "doc-archive"
                }
                png = doc_types[ext]
            except KeyError:
                png = "doc-text"
            span = he.Span(
                he.Str(proj.file_name(f)),
                id_=f"label-file-{f}"
            )
            file_img = he.Img(
                src=base.static_img_src(png),
                title=f,
                alt=f,
                id_=f"img-file-{f}"
            )
            tr = he.Tr(
                he.Td(file_img),
                he.Td(span)
            )
            trs_files.append(tr)
        table = he.Table(*trs_files)
        tr = he.Tr(
            he.Td(),
            he.Td(table),
            he.Td()
        )
        trs.append(tr)

    def new_basic_action(
            action: proj.action_t,
            txt: types.txt_t,
            js: None | str = None,
            icon: types.static_img_t = "play",
            img_txt: types.txt_t = "verb_start"
    ) -> None:
        if js is None:
            js = f"project_basic_action('{action}');"
        a = base.static_img(
            icon,
            img_txt,
            js=js,
            id_=f"img-action-{action}"
        )
        tr = he.Tr(
            he.Td(a),
            he.Td(he.Txt(txt)),
            he.Td()
        )
        trs.append(tr)
        list_files(action)

    def new_upload_action(
            action: proj.action_t,
            f: proj.file_t,
            txt: types.txt_t
    ) -> None:
        input_file = he.Input(
            type_="file",
            id_=f,
            name=f
        )
        a = base.static_img(
            "upload",
            "verb_send",
            js=f"project_upload_action('{action}', '{f}')",
            id_=f"img-action-{action}"
        )
        tr = he.Tr(
            he.Td(a),
            he.Td(he.Txt(txt)),
            he.Td(input_file)
        )
        trs.append(tr)
        list_files(action)

    # div with actions
    new_basic_action(
        "delete",
        "seq_delete_project",
        js="project_delete()",
        icon="trash",
        img_txt="verb_delete"
    )
    new_upload_action(
        "upload-project-archive",
        "zip-tex",
        "seq_upload_latex_archive"
    )
    new_basic_action(
        "compile",
        "seq_compile_latex"
    )
    new_upload_action(
        "upload-answer-sheets",
        "pdf-answer-sheets",
        "seq_upload_answer_sheets"
    )
    new_basic_action(
        "analyse",
        "seq_analyse_answer_sheets"
    )
    #new_basic_action(
    #    "clean-associations",
    #    "seq_clean_associations",
    #    js="project_clean_associations()",
    #    img_txt="verb_delete",
    #    icon="broom"
    #)
    new_basic_action(
        "associate-automatic",
        "seq_associate_automatic"
    )
    new_basic_action(
        "associate-manual-prepare",
        "seq_associate_manual",
        js="project_manual_association_open()"
    )
    new_basic_action(
        "export-scores",
        "seq_generate_scores_and_annotated_sheets"
    )
    new_basic_action(
        "send-annotated-sheets",
        "seq_send_annotated_sheets"
    )
    table_actions = he.Table(
        *trs,
        class_="table-form",
        id_="table-action"
    )
    div_actions = he.Div(
        he.H2(he.Txt("name_actions")),
        table_actions
    )

    # div with data
    input_title = he.Input(
        name="title",
        id_="title",
        size="30"
    )
    input_copies = he.Input(
        value="10",
        name="copies",
        id_="copies",
        size="4"
    )
    input_threshold = he.Input(
        value="0.5",
        name="threshold",
        id_="threshold",
        size="4"
    )
    input_amc_code = he.Input(
        name="amc_code",
        id_="amc_code",
        size="10"
    )
    options_attr = [
        he.Option(he.Str(a.atr_desc), value=a.atr_id)
        for a in sorted(ctx.dbs.query(tables.Attr), key=lambda a: a.atr_desc) 
    ]
    select_attr = he.Select(
        *options_attr,
        name="assoc_attr",
        id_="assoc_attr"
    )
    div_grps = he.Div(id_="div-grps")
    data_spec: list[tuple[types.txt_t, he.Element]] = [
        ("name_title", input_title),
        ("name_copies", input_copies),
        ("name_threshold", input_threshold),
        ("seq_latex_id", input_amc_code),
        ("seq_association_attr", select_attr),
        ("seq_association_source", div_grps)
    ]
    trs = [
        he.Tr(he.Td(he.Txt(txt)), he.Td(elem))
        for txt, elem in data_spec
    ]
    table_data = he.Table(
        *trs,
        class_="table-form",
        id_="table-action-data"
    )
    a_submit_data = base.static_img(
        "checkmark",
        "verb_send",
        js="project_submit_data()",
        style="position: absolute; top: 5px; right: 5px;"
    )
    div_data = he.Div(
        he.H2(he.Txt("name_parameters")),
        table_data,
        a_submit_data,
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
        he.Script("project_manual_association_close()"),
        style="display: flex;"
    )
    
    grps = {
        grp.grp_id: grp.grp_name
        for grp in queries.get_submit_grps(ctx.dbs, session.usr_id(ctx))
    }
    script_init = he.Script([
        f"project_usr_groups = {json.dumps(grps)};",
        "project_init()"
    ])

    elements = he.ElementList(div_main, script_init)

    return fa.responses.HTMLResponse(str(elements))
