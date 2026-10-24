import typing as tp
import typing_extensions as tp_ext

from . import project, txt, item, db


json_response_t = tp_ext.TypedDict(
    "json_response_t",
    {
        "success": bool,
        "msgs": list[str],
        "result": None | tp.Any
    }
)
static_img_t = tp.Literal[
    "add",
    "arrow-clockwise",
    "arrow-down",
    "arrow-left",
    "arrow-right",
    "arrow-up",
    "broom",
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
    "help",
    "home",
    "inbox",
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
    "unlink",
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
    "/exam/oper/export-scores",
    "/exam/oper/register",
    "/help",
    "/img",
    "/inbox/page/list",
    "/inbox/page/msg",
    "/item/page/database-body",
    "/item/page/database-list",
    "/item/page/group",
    "/item/page/main",
    "/item/oper/recursive-deletion",
    "/item/oper/add",
    "/item/oper/add-child",
    "/item/oper/move-child",
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
    "password-change",
    "project-notification-mail"
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
    "err_mail_file_not_found",
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
help_t = tp.Literal[
    "item_submit",
    "project"
]
page_t = tp.Literal[
    "admin",
    "auth",
    "exam",
    "inbox",
    "index",
    "item",
    "mcq",
    "profile",
    "project",
    "stats",
    "ticket"
]
sub_page_t = tp.Literal[
    "admin_database",
    "admin_submit",
    "exam_add",
    "exam_dashboard",
    "exam_database",
    "item_add",
    "item_database",
    "item_groups",
    "item_submit",
    "ticket_account_creation",
    "ticket_eaddr_change",
    "ticket_error",
    "ticket_password_change"
]
class args_oper_t(tp.TypedDict):
    action_params: tp.NotRequired[project.action_params_t]
    action: tp.NotRequired[project.action_t]
    choices: tp.NotRequired[dict[int, bool]]
    content: tp.NotRequired[item.mcq_content_t]
    exm_id: tp.NotRequired[int]
    filters: tp.NotRequired[dict[str, tp.Any]]
    grp_id: tp.NotRequired[None | int]
    itm_code: tp.NotRequired[str]
    itm_exe_or_mcq: tp.NotRequired[tp.Literal["exe", "mcq"]]
    itm_id: tp.NotRequired[int]
    itm_title: tp.NotRequired[str]
    itm_type: tp.NotRequired[item.item_type_t]
    itr_child: tp.NotRequired[int]
    itr_parent: tp.NotRequired[int]
    loc_login: tp.NotRequired[str]
    loc_password_confirm: tp.NotRequired[str]
    loc_password: tp.NotRequired[str]
    move: tp.NotRequired[int]
    next_url: tp.NotRequired[str]
    page_num: tp.NotRequired[int]
    project_code: tp.NotRequired[str]
    project_data: tp.NotRequired[dict[str, tp.Any]]
    query: tp.NotRequired[db.db_query_t | list[db.db_query_t]]
    questions: tp.NotRequired[dict[int, dict[int, bool]]]
    tbl_id: tp.NotRequired[int]
    ticket: tp.NotRequired[str]
    tkt_type: tp.NotRequired[item.ticket_type_t]
    usr_code: tp.NotRequired[str]
    usr_eaddr: tp.NotRequired[str]
    usr_fst_name: tp.NotRequired[str]
    usr_id: tp.NotRequired[None | int]
    usr_name: tp.NotRequired[str]


def oper_code_to_txt(c: oper_code_t) -> txt.txt_t:
    return tp.cast(txt.txt_t, c)


def page_to_txt(page: page_t) -> txt.txt_t:
    return tp.cast(txt.txt_t, f"page_title_{page}")


def sub_page_to_txt(sub: sub_page_t) -> txt.txt_t:
    return tp.cast(txt.txt_t, f"page_title_{sub}")
