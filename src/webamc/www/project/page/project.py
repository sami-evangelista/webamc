#!/usr/bin/env python3

from webamc.www.all import *
from webamc.www.project import router
from webamc.util import fmt, io
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
        for f, fdata in proj.list_files(
            session.usr_code(ctx),
            args["project_code"],
            action
        ):
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
            if fdata is None:
                img = base.static_img(png, title=f, class_="warning")
            else:
                href = base.mkuri(
                    "/project/page/get-file",
                    project_code=args["project_code"],
                    file_name=f
                )
                title = f"{f}  --  {fmt.fmt_datetime(fdata)}"
                img = base.static_img(png, title=title, href=href)
            span_id = "label-file-" + f.replace(".", "-")
            span = he.Span(
                he.Str(f),
                id_=span_id
            )
            tr = he.Tr(
                he.Td(img),
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

    def action_label(
            action: proj.action_t,
            txt: str
    ) -> he.Element:
        result = he.Element(
            he.Span(
                he.Txt(txt),
                id_=f"label-action-{action}"
            ),
            he.Str(" "),
            he.Span(id_=f"status-action-{action}")
        )
        return result

    def new_basic_action(
            action: proj.action_t,
            txt: str,
            js: None | str = None
    ) -> None:
        if js is None:
            js = f"project_basic_action('{action}');"
        a = base.static_img(
            "play",
            "verb_start",
            js=js,
            id_=f"action-{action}"
        )
        tr = he.Tr(
            he.Td(a),
            he.Td(action_label(action, txt)),
            he.Td()
        )
        trs.append(tr)
        list_files(action)

    def new_upload_action(
            action: proj.action_t,
            file_id: proj.file_id_t,
            txt: str
    ) -> None:
        input_file = he.Input(
            type_="file",
            id_=file_id,
            name=file_id
        )
        a = base.static_img(
            "upload",
            "verb_send",
            js=f"project_upload_action('{action}', '{file_id}')",
            id_=f"action-{action}"
        )
        tr = he.Tr(
            he.Td(a),
            he.Td(action_label(action, txt)),
            he.Td(input_file)
        )
        trs.append(tr)
        list_files(action)

    # delete link
    a_delete = base.static_img(
            "trash",
            "verb_delete",
            js="project_delete()"
        )
    tr = he.Tr(
        he.Td(a_delete),
        he.Td(he.Txt("seq_delete_project")),
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
        he.Td(a_clean),
        he.Td(he.Txt("seq_clean_files")),
        he.Td()
    )
    trs.append(tr)

    # div with actions
    new_upload_action(
        "upload-project-archive",
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
        "upload-answer-sheets",
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
        "upload-student-list",
        "student_list",
        "seq_upload_student_list"
    )
    new_basic_action(
        "associate-automatic",
        "seq_associate_automatic"
    )
    new_basic_action(
        "associate-manual-prepare",
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
    script_init = he.Script("project_init()")

    elements = he.ElementList(div_main, script_init)

    return fa.responses.HTMLResponse(str(elements))
