import datetime
import typing as tp
import typing_extensions as tp_ext

from .db import db_query_result_t
from .txt import txt_t


json_response_t = tp_ext.TypedDict(
    "json_response_t",
    {
        "success": bool,
        "msgs": list[str],
        "result": None | tp.Any | db_query_result_t
    }
)

static_img_t = tp.Literal[
    "add",
    "arrow-clockwise",
    "arrow-left",
    "arrow-right",
    "broom",
    "checkbox-checked",
    "checkbox-unchecked",
    "checkmark",
    "database",
    "dismiss",
    "doc-archive",
    "doc-pdf",
    "doc-table",
    "doc-text",
    "edit",
    "exam",
    "group",
    "group-add",
    "inbox",
    "home",
    "list",
    "mail",
    "mcq",
    "menu",
    "person",
    "person-add",
    "play",
    "projects",
    "settings",
    "signout",
    "stats",
    "switch-mode",
    "tag",
    "trash",
    "upload",
    "warning",
    "zoom-in",
    "zoom-out"
]

path_t = tp.Literal[
    "/",
    "/admin/oper/submit",
    "/admin/page/main",
    "/admin/page/table",
    "/auth/oper/login-local",
    "/auth/oper/login-cas",
    "/auth/oper/logout",
    "/auth/page/main",
    "/db/page/input",
    "/db/oper/query",
    "/exam/page/main",
    "/exam/page/dashboard-exam",
    "/exam/oper/register-group",
    "/exam/oper/export-scores",
    "/help",
    "/img",
    "/item/page/database-body",
    "/item/page/database-list",
    "/item/page/group",
    "/item/page/main",
    "/item/oper/save-pack",
    "/item/oper/submit",
    "/mcq/page/form",
    "/mcq/oper/correction",
    "/mcq/oper/finish",
    "/mcq/oper/save",
    "/profile/page/main",
    "/profile/oper/send",
    "/project/page/files",
    "/project/page/get-file",
    "/project/page/get-mail-pdf",
    "/project/page/inbox",
    "/project/page/main",
    "/project/page/manual-association",
    "/project/page/project",
    "/project/oper/action",
    "/project/oper/upload",
    "/project/oper/get-status",
    "/project/oper/set-data",
    "/static",
    "/ticket/page/main",
    "/ticket/oper/account-creation",
    "/ticket/oper/send",
    "/ticket/oper/password-change",
    "/stats/page/dashboard",
]

mail_file_t = tp.Literal[
    "account-creation",
    "eaddr-change",
    "password-change"
]

oper_code_t = tp.Literal[
    "err",
    "err_action_required",
    "err_admin_empty_csv_file",
    "err_admin_no_right_to_update_table",
    "err_admin_table_undeterminable",
    "err_data_required",
    "err_db_invalid_values",
    "err_file_required",
    "err_invalid_eaddr",
    "err_invalid_password_confirm",
    "err_invalid_ticket",
    "err_io",
    "err_item_admin_empty_archive",
    "err_mail_server",
    "err_missing_file",
    "err_project_already_exists",
    "err_project_amc_not_installed",
    "err_project_check_log_file",
    "err_project_invalid_code",
    "err_project_invalid_source",
    "err_project_invalid_tex_archive",
    "err_project_missing_or_invalid_parameter",
    "err_project_not_a_zip_file",
    "err_unknown_eaddr",
    "err_wrong_credentials",
    "succ",
    "succ_login",
    "succ_account_created",
    "succ_project_created",
    "succ_password_changed",
    "succ_ticket_account_creation_sent",
    "succ_ticket_eaddr_change_sent",
    "succ_ticket_password_change_sent"
]

student_monitoring_t = tp_ext.TypedDict("student_monitoring_t", {
    "reg_id": int,
    "usr_login": str,
    "usr_name": str,
    "usr_fst_name": str,
    "status": str,
    "last_seen": datetime.datetime | None,
    "answered_count": int,
    "total_questions": int,
    "score": float
})

exam_monitoring_t = tp_ext.TypedDict("exam_monitoring_t", {
    "exam_status": str,
    "exam_start": datetime.datetime,
    "exam_end": datetime.datetime,
    "students": list[student_monitoring_t]
})

help_t = tp.Literal[
    "item_submit",
    "project_new",
    "project_parameters",
    "project_upload_source"
]


def oper_code_to_txt(c: oper_code_t) -> txt_t:
    return tp.cast(txt_t, c)
