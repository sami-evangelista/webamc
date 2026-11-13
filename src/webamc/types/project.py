import json
import datetime
import typing as tp
from pydantic import TypeAdapter, ValidationError


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
    "publish_annotated_sheets",
    "send_notification_mail"
]

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

project_history_t = list[tuple[action_t, datetime.datetime, bool]]

project_actions_done_t = dict[action_t, bool]

class file_status_t(tp.TypedDict):
    exists: bool
    size: tp.Optional[int]
    date: tp.Optional[datetime.datetime]


ta_project_actions_done = TypeAdapter(project_actions_done_t)
def check_project_actions_done(data: str) -> project_actions_done_t:
    try:
        data = json.loads(data)
        ta_project_actions_done.validate_python(data)
    except (ValidationError, json.decoder.JSONDecodeError) as ex:
        raise ValueError from ex
    return tp.cast(project_actions_done_t, data)


ta_project_history = TypeAdapter(project_history_t)
def check_project_history(data: str) -> project_history_t:
    try:
        data = json.loads(data)
        ta_project_history.validate_python(data)
    except (ValidationError, json.decoder.JSONDecodeError) as ex:
        raise ValueError from ex
    return tp.cast(project_history_t, data)
