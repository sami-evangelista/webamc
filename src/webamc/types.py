import datetime
import typing as tp
import typing_extensions as tp_ext


def literal_type_values(t: tp._SpecialForm) -> set[tp.Any]:
    return set(tp.get_args(t))


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
        "dev": bool,
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
    "play",
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


load_single_result_t = tp.TypedDict(
    "load_single_result_t",
    {
        "status": tp.Literal[0, 1, 2],
        "msg": str
    }
)
load_result_t = list[load_single_result_t]


txt_t = tp.Literal[
    "col_desc_adm_id",
    "col_desc_adm_tbl",
    "col_desc_adm_usr",
    "col_desc_atr_id",
    "col_desc_atr_code",
    "col_desc_atr_desc",
    "col_desc_cas_enabled",
    "col_desc_cas_id",
    "col_desc_cas_login",
    "col_desc_cas_usr",
    "col_desc_exm_duration",
    "col_desc_exm_mcq",
    "col_desc_exm_start",
    "col_desc_grp_id",
    "col_desc_grp_name",
    "col_desc_grp_parent",
    "col_desc_itm_code",
    "col_desc_itm_date",
    "col_desc_itm_difficulty",
    "col_desc_itm_rnd",
    "col_desc_itm_standalone",
    "col_desc_itm_title",
    "col_desc_itm_type",
    "col_desc_itm_usr",
    "col_desc_itm_visible",
    "col_desc_loc_enabled",
    "col_desc_loc_id",
    "col_desc_loc_login",
    "col_desc_loc_password",
    "col_desc_loc_usr",
    "col_desc_mcq_mode",
    "col_desc_tag_color",
    "col_desc_tag_desc",
    "col_desc_tag_id",
    "col_desc_tag_name",
    "col_desc_tbl_id",
    "col_desc_tbl_name",
    "col_desc_uat_usr",
    "col_desc_uat_attr",
    "col_desc_uat_value",
    "col_desc_ugp_grp",
    "col_desc_ugp_id",
    "col_desc_ugp_right",
    "col_desc_ugp_usr",
    "col_desc_usr_code",
    "col_desc_usr_eaddr",
    "col_desc_usr_fst_name",
    "col_desc_usr_id",
    "col_desc_usr_name",
    "err",
    "err_action_required",
    "err_admin_empty_csv_file",
    "err_admin_no_right_to_update_table",
    "err_admin_table_undeterminable",
    "err_data_required",
    "err_db_invalid_values",
    "err_file_required",
    "err_http_403",
    "err_http_404",
    "err_http_422",
    "err_http_500",
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
    "info_exam_finished",
    "info_no_exam_available",
    "info_no_mcq_available",
    "info_please_wait",
    "info_progress_saved",
    "name_actions",
    "name_confirmation",
    "name_copies",
    "name_date",
    "name_dashboard",
    "name_details",
    "name_exam",
    "name_exercise",
    "name_groups",
    "name_mcq",
    "name_minutes",
    "name_no",
    "name_page",
    "name_parameters",
    "name_question",
    "name_review",
    "name_rights",
    "name_sender",
    "name_statement",
    "name_submission",
    "name_table",
    "name_tags",
    "name_threshold",
    "name_title",
    "name_type",
    "name_view",
    "name_yes",
    "op_after",
    "op_before",
    "op_diff",
    "op_eq",
    "op_gt",
    "op_like",
    "op_lt",
    "op_notlike",
    "page_title_administration",
    "page_title_administration_database",
    "page_title_administration_submit_form",
    "page_title_authentication",
    "page_title_authentication_account_creation",
    "page_title_authentication_login_cas",
    "page_title_authentication_login_local",
    "page_title_authentication_password_change",
    "page_title_eaddr_change",
    "page_title_exam",
    "page_title_exam_creation",
    "page_title_exam_dashboard",
    "page_title_exam_database",
    "page_title_index",
    "page_title_item",
    "page_title_item_database",
    "page_title_item_groups",
    "page_title_item_pack",
    "page_title_item_submit_form",
    "page_title_password_change",
    "page_title_profile",
    "page_title_profile_group",
    "page_title_profile_personal_data",
    "page_title_project",
    "page_title_project_inbox",
    "page_title_project_main",
    "page_title_signout",
    "page_title_ticket_error",
    "param_err_invalid_duplicate_value",
    "param_err_invalid_null_value",
    "param_err_invalid_value",
    "param_seq_next_question",
    "param_seq_previous_question",
    "param_seq_registrations_done",
    "param_seq_switch_mode",
    "param_seq_users_registered",
    "qst_confirmation_project_associate_automatic",
    "qst_confirmation_project_compile",
    "qst_confirmation_project_clean_associations",
    "qst_confirmation_project_delete",
    "qst_exam_deletion_confirmation",
    "qst_exam_deletion_confirmation",
    "qst_item_deletion_confirmation",
    "qst_item_row_confirmation",
    "qst_mcq_form_confirmation",
    "qst_restart_mcq_confirmation",
    "seq_administrate_this_mcq",
    "seq_analyse_answer_sheets",
    "seq_associate_automatic",
    "seq_associate_manual",
    "seq_association_attr",
    "seq_association_source",
    "seq_authentify_with_server",
    "seq_clean_associations",
    "seq_compile_latex",
    "seq_confirmation_request",
    "seq_csv_file",
    "seq_delete_project",
    "seq_enter_new_eaddr",
    "seq_error_messages",
    "seq_generate_scores_and_annotated_sheets",
    "seq_information_messages",
    "seq_items_found",
    "seq_latex_id",
    "seq_manual_association",
    "seq_project_file_log_webamc",
    "seq_project_file_ods_scores",
    "seq_project_file_pdf_answer_sheets",
    "seq_project_file_pdf_correction",
    "seq_project_file_pdf_subject",
    "seq_project_file_source",
    "seq_project_file_zip_annotated_sheets",
    "seq_project_file_zip_sheets",
    "seq_new_project",
    "seq_new_row",
    "seq_no_name",
    "seq_records_found",
    "seq_select_an_exam",
    "seq_select_a_project",
    "seq_send_annotated_sheets",
    "seq_upload_answer_sheets",
    "seq_upload_latex_archive",
    "seq_upload_student_list",
    "seq_warning_messages",
    "seq_zip_file",
    "succ",
    "succ_account_created",
    "succ_eaddr_changed",
    "succ_login",
    "succ_password_changed",
    "succ_project_created",
    "succ_ticket_account_creation_sent",
    "succ_ticket_eaddr_change_sent",
    "succ_ticket_password_change_sent",
    "tbl_desc_admin",
    "tbl_desc_attr",
    "tbl_desc_cas_auth",
    "tbl_desc_grp",
    "tbl_desc_local_auth",
    "tbl_desc_tag",
    "tbl_desc_tbl",
    "tbl_desc_usr",
    "tbl_desc_usr_attr",
    "tbl_desc_usr_grp",
    "verb_add",
    "verb_administrate",
    "verb_answer",
    "verb_cancel",
    "verb_close",
    "verb_create",
    "verb_delete",
    "verb_filter",
    "verb_send",
    "verb_start",
    "verb_validate",
    "warning_exam_deletion_forbidden"
]

help_t = tp.Literal[
    "project_new",
    "project_parameters",
    "project_upload_source"
]


def oper_code_to_txt(c: oper_code_t) -> txt_t:
    return tp.cast(txt_t, c)
