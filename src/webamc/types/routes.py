import typing as tp
import typing_extensions as tp_ext

from . import item, project


# arguments of ticket routes
args_route_ticket_oper_account_creation_t = tp_ext.TypedDict(
    "args_route_ticket_oper_account_creation_t",
    {
        "ticket": str,
        "usr_code": str,
        "usr_eaddr": str,
        "usr_fst_name": str,
        "usr_name": str,
        "loc_password": str,
        "loc_password_confirm": str
    }
)
args_route_ticket_oper_send_t = tp_ext.TypedDict(
    "args_route_ticket_oper_send_t",
    {
        "usr_eaddr": str,
        "tkt_type": item.ticket_type_t
    }
)
args_route_ticket_oper_password_change_t = tp_ext.TypedDict(
    "args_route_ticket_oper_password_change_t",
    {
        "ticket": str,
        "loc_password": str,
        "loc_password_confirm": str
    }
)


# arguments of item routes
args_route_item_oper_add_t = tp_ext.TypedDict(
    "args_route_item_oper_add_t",
    {
        "itm_code": str,
        "itm_title": str,
        "itm_type": item.item_type_t,
        "type": tp.Literal["exe", "mcq"]
    }
)
args_route_item_oper_add_child_t = tp_ext.TypedDict(
    "args_route_item_oper_add_child_t",
    {
        "itr_parent": int,
        "itr_child": int
    }
)
args_route_item_oper_move_child_t = tp_ext.TypedDict(
    "args_route_item_oper_move_child_t",
    {
        "itr_parent": int,
        "itr_child": int,
        "move": int
    }
)
args_route_item_item_t = tp_ext.TypedDict(
    "args_route_item_item_t",
    {
        "itm_id": int
    }
)


# arguments of admin routes
args_route_admin_page_table_t = tp_ext.TypedDict(
    "args_route_admin_page_table_t",
    {
        "tbl_id": int,
        "page_num": int,
        "filters": dict[str, tp.Any]
    }
)
args_route_admin_tbl_t = tp_ext.TypedDict(
    "args_route_admin_tbl_t",
    {
        "tbl_id": int
    }
)


# arguments of auth routes
args_route_auth_oper_login_local_t = tp_ext.TypedDict(
    "args_route_auth_oper_login_local_t", {
        "loc_login": str,
        "loc_password": str
    }
)


# arguments of project routes
args_route_project_oper_action_t = tp_ext.TypedDict(
    "args_route_project_oper_action_t", {
        "action": project.action_t,
        "project_code": str,
        "action_params": project.action_params_t
    }
)
args_route_project_page_manual_association_t = tp_ext.TypedDict(
    "args_route_project_page_manual_association_t", {
        "project_code": str,
        "action_params": project.action_params_t
    }
)
args_route_project_project_code_t = tp_ext.TypedDict(
    "args_route_project_project_code_t", {
        "project_code": str
    }
)


# arguments of exam routes
args_route_exam_exam_t = tp_ext.TypedDict(
    "args_route_exam_exam_t",
    {
        "exm_id": int
    }
)
args_route_exam_oper_register_group_t = tp_ext.TypedDict(
    "args_route_exam_oper_register_group_t",
    {
        "exm_id": int,
        "grp_id": int
    }
)


# arguments of exam routes
args_route_mcq_result_t = tp_ext.TypedDict(
    "args_route_mcq_result_t",
    {
        "itm_id": int,
        "choices": dict[int, bool],
        "questions": dict[int, dict[int, bool]]
    }
)
