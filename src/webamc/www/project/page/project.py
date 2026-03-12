#!/usr/bin/env python3

from webamc.www.all import *
from webamc.www.project import router
from webamc import project as proj


def page(
        ctx: context.Context,
        args: router.args_project_code_t
) -> fa.Response:
    trs: list[he.Element] = list()

    def new_basic_action(
            action: None | proj.action_t,
            txt: str,
            js: None | str = None
    ) -> None:
        nonlocal trs
        span = he.Span(he.Txt(txt))
        if action is None:
            img: he.Element = he.Empty()
        else:
            img = he.Img(
                src=base.static_img_src("checkbox-unchecked"),
                id_=f"img-status-{action}"
            )
            span["id"] = f"label-action-{action}"
        if js is None:
            assert action is not None
            js = f"project_basic_action('{action}');"
        a = base.static_img(
            "checkmark",
            "verb_start",
            js=js
        )
        tr = he.Tr(
            he.Td(img),
            he.Td(span),
            he.Td(a),
            he.Td()
        )
        trs.append(tr)

    def new_upload_action(
            file_id: proj.file_id_t,
            txt: str
    ) -> None:
        img = he.Img(
            src=base.static_img_src("checkbox-unchecked"),
            id_=f"img-status-{file_id}"
        )
        input_file = he.Input(
            type_="file",
            id_=file_id,
            name=file_id,
        )
        a = base.static_img(
            "upload",
            "verb_send",
            js=f"project_upload_action('{file_id}')"
        )
        tr = he.Tr(
            he.Td(img),
            he.Td(he.Span(he.Txt(txt), id_=f"label-file-{file_id}")),
            he.Td(input_file),
            he.Td(a)
        )
        trs.append(tr)

    # delete link
    a_delete = base.static_img(
            "trash",
            "verb_delete",
            js="project_delete()"
        )
    tr = he.Tr(
        he.Td(),
        he.Td(he.Txt("seq_delete_project")),
        he.Td(a_delete),
        he.Td()
    )
    trs.append(tr)

    # clean link
    a_clean = base.static_img(
            "broom",
            "verb_clean",
            js="project_clean_files()"
        )
    tr = he.Tr(
        he.Td(),
        he.Td(he.Txt("seq_clean_files")),
        he.Td(a_clean),
        he.Td()
    )
    trs.append(tr)

    # div with actions
    new_upload_action(
        "project_archive",
        "seq_upload_latex_archive"
    )
    new_basic_action(
        "compile",
        "seq_compile_latex"
    )
    new_basic_action(
        "extract-layout-data",
        "seq_extract_layout_data"
    )
    new_basic_action(
        "generate-sheets",
        "seq_generate_sheets"
    )
    new_upload_action(
        "answer_sheets",
        "seq_upload_answer_sheets"
    )
    new_basic_action(
        "extract-answer-sheets",
        "seq_extract_answer_sheets"
    )
    new_basic_action(
        "analyse-answer-sheets",
        "seq_analyse_answer_sheets"
    )
    new_basic_action(
        "extract-scoring-data",
        "seq_extract_scoring_data"
    )
    new_basic_action(
        "compute-scores",
        "seq_compute_scores"
    )
    new_upload_action(
        "student_list",
        "seq_upload_student_list"
    )
    new_basic_action(
        "associate-automatic",
        "seq_associate_automatic"
    )
    new_basic_action(
        None,
        "seq_associate_manual",
        "project_manual_association_open()"
    )
    new_basic_action(
        "export-scores",
        "seq_export_scores"
    )
    new_basic_action(
        "annotate",
        "seq_generate_annotated_sheets"
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

    # div with parameters
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
    input_id_key = he.Input(
        name="id_key",
        id_="id_key",
        size="10"
    )
    input_eaddr = he.Input(
        name="eaddr",
        id_="eaddr",
        size="10"
    )
    trs = [
        he.Tr(he.Td(he.Txt(txt)), he.Td(elem))
        for txt, elem in [
                ("name_title", input_title),
                ("name_copies", input_copies),
                ("name_threshold", input_threshold),
                ("seq_latex_id", input_amc_code),
                ("seq_csv_column_id", input_id_key),
                ("seq_csv_column_eaddr", input_eaddr)
        ]
    ]
    table_parameters = he.Table(
        *trs,
        class_="table-form",
        id_="table-action-params"
    )
    a_submit_parameters = base.static_img(
        "checkmark",
        "verb_send",
        js="project_submit_params()",
        style="position: absolute; top: 5px; right: 5px;"
    )
    div_parameters = he.Div(
        he.H2(he.Txt("name_parameters")),
        table_parameters,
        a_submit_parameters,
        style="position: relative;"
    )

    # div with files
    div_files = he.Div(
        id_="div-files"
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
        div_parameters,
        div_files,
        id_="div-right",
        style="min-width: 400px; position: relative;"
    )

    div_main = he.Div(
        div_left,
        div_separator,
        div_right,
        style="display: flex;"
    )
    script_init = he.Script("project_init()")

    elements = he.ElementList(div_main, script_init)

    return fa.responses.HTMLResponse(str(elements))
