#!/usr/bin/env python3

from webamc.www.all import *


router = fa.APIRouter()

args_page_table_t = tp_ext.TypedDict("args_page_table_t", {
    "tbl_id": int,
    "page_num": int,
    "filters": dict[str, tp.Any]
})

args_page_admin_t = tp_ext.TypedDict("args_page_admin_t", {
    "tbl_id": int
})


@router.post("/admin/oper/submit")
def route_oper_submit(
        req: fa.Request,
        csv_file: fa.UploadFile
) -> fa.Response:
    from .oper import submit
    ctx = context.Context(req)
    return fa.responses.JSONResponse(submit.data(ctx, csv_file))


@router.post("/admin/page/table")
def route_page_table(
        req: fa.Request,
        args: args_page_table_t
) -> fa.Response:
    from .page import table
    with context.Context(req) as ctx:
        return table.page(ctx, args)


@router.get("/admin/page/main")
def route_page_main(
        req: fa.Request,
        sub_page: None | str = None,
        tbl_id: int | None = None
) -> fa.Response:
    from .page import submit_form, database
    layout: base.page_layout_t = {
        "title": "page_title_administration",
        "path": "/admin/page/main",
        "default": "database",
        "sub_pages": {
            "database": ("database", database.page),
            "submit_form": ("upload", submit_form.page)
        }
    }
    with context.Context(req) as ctx:
        session.check_admin(ctx)
        result = base.gen_composite_page(
            ctx, layout, sub_page, sub_page_args={"tbl_id": tbl_id}
        )
        return result
