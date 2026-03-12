#!/usr/bin/env python3

import datetime
import typing as tp
import typing_extensions as tp_ext


lang_t = tp.Literal[
    "en",
    "fr"
]

conf_t = tp_ext.TypedDict(
    "conf_t",
    {
        "base_url": str,
        "auth_account_creation_enabled": bool,
        "auth_cas_enabled": bool,
        "auth_local_enabled": bool,
        "cas_server": str,
        "cas_server_name": str,
        "cas_version": int,
        "date_format": None | str,
        "date_locale": str,
        "datetime_format": None | str,
        "db_host": str,
        "db_name": str,
        "db_password": str,
        "db_port": None | int,
        "db_user": str,
        "debug": bool,
        "icon_size": int,
        "inbox_dir": str,
        "json_file_pack": str,
        "key_qst_next": str,
        "key_qst_prev": str,
        "key_switch_mode": str,
        "lang": lang_t,
        "log_file": None | str,
        "mails_dir": None | str,
        "password_ticket_validity": int,
        "projects_dir": str,
        "root_path": str,
        "secret_key": str,
        "service_name": str,
        "smtp_auth": bool,
        "smtp_eaddr_from": str,
        "smtp_host": str,
        "smtp_password": str,
        "smtp_port": int,
        "smtp_user": str,
        "tex2pdf_exe": str,
        "tex2pdf_exe_args": list[str],
        "tex_envs_choices": list[str],
        "tex_envs_question": list[str],
        "tex_envs_question_mult": list[str],
        "tex_file_exercise": str,
        "tex_file_header": str,
        "tex_file_mcq": str,
        "tex_file_question_prefix": str,
        "tex_file_webamc": str,
        "tex_macros_choice": list[str],
        "tex_macros_choice_correct": list[str],
        "tex_macros_lastchoices": list[str],
        "ticket_length": int
    },
    total=True
)


question_type_t = tp.Literal[0, 1]
QUESTION_TYPE_SINGLE: question_type_t = 0
QUESTION_TYPE_MULTI: question_type_t = 1


mcq_mode_t = tp.Literal[0, 1]
MCQ_MODE_EXAM: mcq_mode_t = 0
MCQ_MODE_REVIEW: mcq_mode_t = 1


item_type_t = tp.Literal[0, 1, 2, 3]
ITEM_TYPE_CHOICE: item_type_t = 0
ITEM_TYPE_EXERCISE: item_type_t = 1
ITEM_TYPE_PACK: item_type_t = 2
ITEM_TYPE_QUESTION: item_type_t = 3


item_difficulty_t = tp.Literal[1, 2, 3, 4, 5]
ITEM_MIN_DIFFICULTY: item_difficulty_t = 1
ITEM_MAX_DIFFICULTY: item_difficulty_t = 5


usr_right_t = tp.Literal[1, 2]
USR_RIGHT_VIEW: usr_right_t = 1
USR_RIGHT_SUBMIT: usr_right_t = 2


ticket_type_t = tp.Literal[0, 1, 2]
TICKET_PASSWORD_CHANGE: ticket_type_t = 0
TICKET_EADDR_CHANGE: ticket_type_t = 1
TICKET_ACCOUNT_CREATION: ticket_type_t = 2


pack_op_t = tp.Literal[
    "all",
    "shuf",
    "sort",
    "head",
    "with-code",
    "with-difficulty",
    "with-tag"
]
dict_pack_spec_t = tp_ext.TypedDict(
    "dict_pack_spec_t",
    {
        "op": pack_op_t,
        "arg": tp.Any,
        "rev": bool,
        "content": "pack_spec_t"
    },
    total=False
)
pack_spec_t = tp.Union[list["dict_pack_spec_t"], dict_pack_spec_t]


# types related to database
db_base_val_t = str | int | bool | datetime.date | datetime.datetime | None
db_map_t = dict[str, db_base_val_t]
db_query_result_t = tp_ext.TypedDict(
    "db_query_result_t",
    {
        "values": list[list[db_map_t]] | list[db_map_t],
        "readable_values": list[list[db_map_t]] | list[db_map_t]
    },
    total=False
)
db_where_t = tp_ext.TypedDict(
    "db_where_t",
    {
        "col": str,
        "op": tp.Literal["=", "like"],
        "val": db_base_val_t
    }
)
db_query_type_t = tp.Literal["delete", "insert", "select", "update"]
db_query_t = tp_ext.TypedDict(
    "db_query_t",
    {
        "type": db_query_type_t,
        "table": str,
        "values": db_map_t,
        "where": list[db_where_t]
    },
    total=False
)


item_mdata_t = tp.Literal[
    "CODE",
    "DIFFICULTY",
    "RND",
    "STANDALONE",
    "TAG",
    "TITLE",
    "VISIBLE"
]

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
    "password",
    "person",
    "person-add",
    "projects",
    "settings",
    "server",
    "signout",
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
    "/project/oper/get-data",
    "/project/oper/get-status",
    "/project/oper/set-data",
    "/static",
    "/ticket/page/main",
    "/ticket/oper/account-creation",
    "/ticket/oper/send",
    "/ticket/oper/password-change"
]

mail_file_t = tp.Literal[
    "account-creation",
    "eaddr-change",
    "password-change"
]

oper_code_t = tp.Literal[
    "err",
    "err_action_required",
    "err_amc_not_installed",
    "err_check_log_file",
    "err_invalid_csv_file",
    "err_invalid_eaddr",
    "err_invalid_password_confirm",
    "err_invalid_project_code",
    "err_invalid_project_title",
    "err_invalid_tex_archive",
    "err_invalid_ticket",
    "err_io",
    "err_mail_server",
    "err_missing_file",
    "err_missing_or_invalid_parameter",
    "err_not_a_zip_file",
    "err_project_already_exists",
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


load_single_result_t = tp.TypedDict(
    "load_single_result_t",
    {
        "status": tp.Literal[0, 1, 2],
        "msg": str
    }
)
load_result_t = list[load_single_result_t]


def literal_type_values(t: tp._SpecialForm) -> list[tp.Any]:
    return list(tp.get_args(t))
