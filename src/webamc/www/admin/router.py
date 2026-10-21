from webamc.www.all import *


router = fa.APIRouter()


@router.post("/admin/oper/submit")
def route_oper_submit(
        req: fa.Request,
        csv_file: fa.UploadFile
) -> fa.Response:
    from .oper import submit
    ctx = context.Context(req)
    return submit.data(ctx, csv_file)


@router.post("/admin/page/table")
def route_page_table(
        req: fa.Request,
        args: types.args_route_admin_page_table_t
) -> fa.Response:
    from .page import table
    with context.Context(req) as ctx:
        return table.page(ctx, args)


@router.get("/admin/page/main")
def route_page_main(
        req: fa.Request,
        sub_page: None | types.sub_page_t = None,
        tbl_id: int | None = None
) -> fa.Response:
    from .page import submit_form, database
    layout: base.page_layout_t = {
        "page": "admin",
        "default": "admin_database",
        "sub_pages": {
            "admin_database": {
                "dev": False,
                "img": "database",
                "gen": database.page
            },
            "admin_submit": {
                "dev": False,
                "img": "upload",
                "gen": submit_form.page
            }
        }
    }
    with context.Context(req) as ctx:
        session.check_admin(ctx)
        result = base.gen_composite_page(
            ctx, layout, sub_page, sub_page_args={"tbl_id": tbl_id}
        )
        return result
