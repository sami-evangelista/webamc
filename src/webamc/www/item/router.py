#!/usr/bin/env python3

from webamc.www.all import *


router = fa.APIRouter()

args_oper_save_pack_t = tp_ext.TypedDict("args_oper_save_pack_t", {
    "code": str,
    "title": str,
    "pack": tp.Any
})
args_page_item_t = tp_ext.TypedDict("args_page_item_t", {
    "itm_id": int
})


@router.post("/item/oper/save-pack")
def route_oper(
        req: fa.Request,
        args: args_oper_save_pack_t
) -> fa.Response:
    from .oper import save_pack
    with context.Context(req) as ctx:
        return save_pack.data(ctx, args)


@router.post("/item/oper/submit")
def route_oper_submit(
        req: fa.Request,
        zip_file: fa.UploadFile
) -> fa.Response:
    from .oper import submit
    with context.Context(req) as ctx:
        return submit.data(ctx, zip_file)


@router.post("/item/page/database-list")
def route_page_database_list(
        req: fa.Request,
        filters: dict[str, tp.Any]
) -> fa.Response:
    from .page import database_list
    with context.Context(req) as ctx:
        return database_list.page(ctx, filters)


@router.get("/item/page/database-body")
def route_page_database_body(
        req: fa.Request,
        itm_id: int
) -> fa.Response:
    from .page import database_body
    with context.Context(req) as ctx:
        return database_body.page(ctx, itm_id)


@router.get("/item/page/group")
def route_page_group(
        req: fa.Request,
        grp_id: int
) -> fa.Response:
    from .page import group
    with context.Context(req) as ctx:
        return fa.responses.HTMLResponse(str(group.page(ctx, grp_id)))


@router.get("/item/page/main")
def route_page_main(
        req: fa.Request,
        sub_page: None | str = None,
        itm_id: None | int = None
) -> fa.Response:
    from .page import database, submit_form, pack, groups
    layout: base.page_layout_t = {
        "title": "page_title_item",
        "path": "/item/page/main",
        "default": "database",
        "sub_pages": {
            "database": ("database", database.page),
            "submit_form": ("upload", submit_form.page),
            "pack": ("add", pack.page),
            "groups": ("group", groups.page)
        }
    }
    with context.Context(req) as ctx:
        session.check_logged_in(ctx)
        result = base.gen_composite_page(
            ctx, layout, sub_page, sub_page_args={"itm_id": itm_id}
        )
    return result
