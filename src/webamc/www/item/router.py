from webamc.www.all import *


router = fa.APIRouter()

args_oper_add_t = tp_ext.TypedDict("args_oper_add_t", {
    "itm_code": str,
    "itm_title": str,
    "itm_type": types.item_type_t,
    "type": tp.Literal["exe", "mcq"]
})
args_oper_add_child_t = tp_ext.TypedDict("args_oper_add_child_t", {
    "itr_parent": int,
    "itr_child": int
})
args_oper_move_child_t = tp_ext.TypedDict("args_oper_move_child_t", {
    "itr_parent": int,
    "itr_child": int,
    "move": int
})
args_item_t = tp_ext.TypedDict("args_item_t", {
    "itm_id": int
})


@router.post("/item/oper/add")
def route_oper_add(
        req: fa.Request,
        args: args_oper_add_t
) -> fa.Response:
    from .oper import add
    with context.Context(req) as ctx:
        if not session.has_submission_right(ctx):
            raise fa.HTTPException(status_code=403)
        return add.data(ctx, args)


@router.post("/item/oper/add-child")
def route_oper_add_child(
        req: fa.Request,
        args: args_oper_add_child_t
) -> fa.Response:
    from .oper import add_child
    with context.Context(req) as ctx:
        if not session.has_submission_right(ctx):
            raise fa.HTTPException(status_code=403)
        return add_child.data(ctx, args)


@router.post("/item/oper/move-child")
def route_oper_move_child(
        req: fa.Request,
        args: args_oper_move_child_t
) -> fa.Response:
    from .oper import move_child
    with context.Context(req) as ctx:
        if not session.has_submission_right(ctx):
            raise fa.HTTPException(status_code=403)
        return move_child.data(ctx, args)


@router.post("/item/oper/submit")
def route_oper_submit(
        req: fa.Request,
        zip_file: fa.UploadFile
) -> fa.Response:
    from .oper import submit
    with context.Context(req) as ctx:
        if not session.has_submission_right(ctx):
            raise fa.HTTPException(status_code=403)
        return submit.data(ctx, zip_file)


@router.post("/item/oper/recursive-deletion")
def route_oper_recursive_deletion(
        req: fa.Request,
        args: args_item_t
) -> fa.Response:
    from .oper import recursive_deletion
    with context.Context(req) as ctx:
        if not session.has_submission_right(ctx):
            raise fa.HTTPException(status_code=403)
        return recursive_deletion.data(ctx, args)


@router.post("/item/page/database-list")
def route_page_database_list(
        req: fa.Request,
        filters: dict[str, tp.Any]
) -> fa.Response:
    from .page import database_list
    with context.Context(req) as ctx:
        if not session.has_submission_right(ctx):
            raise fa.HTTPException(status_code=403)
        return database_list.page(ctx, filters)


@router.get("/item/page/database-body")
def route_page_database_body(
        req: fa.Request,
        itm_id: int,
        iti_num: int,
) -> fa.Response:
    from .page import database_body
    with context.Context(req) as ctx:
        if not session.has_submission_right(ctx):
            raise fa.HTTPException(status_code=403)
        return database_body.page(ctx, itm_id, iti_num)


@router.get("/item/page/group")
def route_page_group(
        req: fa.Request,
        grp_id: int
) -> fa.Response:
    from .page import group
    with context.Context(req) as ctx:
        if not session.has_submission_right(ctx):
            raise fa.HTTPException(status_code=403)
        return fa.responses.HTMLResponse(str(group.page(ctx, grp_id)))


@router.get("/item/page/main")
def route_page_main(
        req: fa.Request,
        sub_page: None | types.sub_page_t = None,
        itm_id: None | int = None
) -> fa.Response:
    from .page import database, submit, add, groups
    layout: base.page_layout_t = {
        "page": "item",
        "default": "item_database",
        "sub_pages": {
            "item_database": {
                "dev": False,
                "img": "database",
                "gen": database.page
            },
            "item_submit": {
                "dev": False,
                "img": "upload",
                "gen": submit.page
            },
            "item_add": {
                "dev": True,
                "img": "add",
                "gen": add.page
            },
            "item_groups": {
                "dev": False,
                "img": "group",
                "gen": groups.page
            }
        }
    }
    with context.Context(req) as ctx:
        if not session.has_submission_right(ctx):
            raise fa.HTTPException(status_code=403)
        result = base.gen_composite_page(
            ctx, layout, sub_page, sub_page_args={"itm_id": itm_id}
        )
    return result
