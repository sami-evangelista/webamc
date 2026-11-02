import datetime
import typing as tp
import typing_extensions as tp_ext


action_t = tp.Literal[
    "analyse",
    "associate_automatic",
    "associate_manual_prepare",
    "associate_manual",
    "clean_associations",
    "compile",
    "delete",
    "export_scores",
    "new",
    "upload_answer_sheets",
    "upload_source",
    "send_annotated_sheets",
    "send_notification_mail"
]

source_type_t = tp.Literal[
    "tex",
    "txt"
]

cmd_t = tp.Literal[
    "decode",
    "analyse",
    "annotate",
    "association",
    "association-auto",
    "clean_associations",
    "prepare_s",
    "note",
    "export",
    "meptex",
    "prepare_bk",
    "getimages",
    "imprime",
    "read-pdfform"
]

class data_t(tp_ext.TypedDict):
    assoc_attr: tp.NotRequired[int]
    code: tp.NotRequired[str]
    title: tp.NotRequired[str]
    amc_code: tp.NotRequired[str]
    threshold: tp.NotRequired[float]
    copies: tp.NotRequired[int]
    groups: tp.NotRequired[list[int]]

class action_params_t(tp_ext.TypedDict):
    copy: tp.NotRequired[None | int]
    student: tp.NotRequired[None | int]
    id: tp.NotRequired[None | str]

file_t = tp.Literal[
    "csv_list",
    "json_status",
    "log_webamc",
    "ods_scores",
    "pdf_answer_sheets",
    "pdf_correction",
    "pdf_subject",
    "sqlite_association",
    "sqlite_capture",
    "source",
    "tex_main",
    "txt_main",
    "xy_calage",
    "zip_annotated_sheets",
    "zip_sheets",
    "zip_tex"
]

class file_status_t(tp.TypedDict):
    exists: bool
    size: None | int
    date: None | datetime.datetime

class status_t(tp.TypedDict):
    source_type: source_type_t
    done: dict[action_t, bool]
    doable: dict[action_t, tuple[bool, list[tuple[str, str]]]]
    history: list[tuple[action_t, datetime.datetime, bool]]
    data: data_t
    files: dict[file_t, file_status_t]
    warning: dict[action_t, bool]
