from webamc.www.all import *


router = fa.APIRouter()


@router.post("/admin/oper/submit")
def oper_submit(
        req: fa.Request,
        csv_file: fa.UploadFile
) -> fa.Response:
    from .oper import submit
    ctx = context.Context(req)
    return submit.data(ctx, csv_file)


@router.post("/admin/oper/gen-random")
def oper_gen_random(req: fa.Request, args: types.args_oper_t) -> fa.Response:
    from .oper import gen_random
    with context.Context(req) as ctx:
        return gen_random.data(ctx, args)


@router.post("/admin/page/table")
def page_table(req: fa.Request, args: types.args_oper_t) -> fa.Response:
    from .page import table
    with context.Context(req) as ctx:
        return table.page(ctx, args)


@router.get("/admin/page/main")
def page_main(
        req: fa.Request,
        sub_page: tp.Optional[types.sub_page_t] = None,
        tbl_id: tp.Optional[int] = None
) -> fa.Response:
    from .page import submit_form, database, random_form
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
        if session.is_root(ctx):
            layout["sub_pages"]["admin_random_form"] = {
                "dev": True,
                "img": "random",
                "gen": random_form.page
            }
        result = base.gen_composite_page(
            ctx, layout, sub_page, sub_page_args={"tbl_id": tbl_id}
        )
        return result
