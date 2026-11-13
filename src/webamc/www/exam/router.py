from webamc.www.all import *


router = fa.APIRouter()


@router.get("/exam/oper/export-scores")
def oper_export_scores(
    req: fa.Request,
    exm_id: int
) -> fa.Response:
    from .oper import export_scores
    with context.Context(req) as ctx:
        return export_scores.generate_excel_scores(ctx=ctx, exm_id=exm_id)


@router.post("/exam/oper/register")
def oper_register(req: fa.Request, args: types.args_oper_t) -> fa.Response:
    from .oper import register
    with context.Context(req) as ctx:
        return register.data(ctx, args)


@router.post("/exam/oper/publish-scores")
def oper_publish_scores(
        req: fa.Request,
        args: types.args_oper_t
) -> fa.Response:
    from .oper import publish_scores
    with context.Context(req) as ctx:
        return publish_scores.data(ctx, args)


@router.post("/exam/oper/send-notifications")
def oper_send_notifications(
        req: fa.Request,
        args: types.args_oper_t
) -> fa.Response:
    from .oper import send_notifications
    with context.Context(req) as ctx:
        return send_notifications.data(ctx, args)


@router.post("/exam/page/dashboard")
def page_dashboard(req: fa.Request, args: types.args_oper_t) -> fa.Response:
    from .page import dashboard
    with context.Context(req) as ctx:
        return dashboard.page(ctx, args)


@router.get("/exam/page/main")
def exam_page(
        req: fa.Request,
        sub_page: None | types.sub_page_t = None,
        exm_id: None | int = None
) -> fa.Response:
    from .page import add, database
    layout: base.page_layout_t = {
        "page": "exam",
        "default": "exam_database",
        "sub_pages": {
            "exam_database": {
                "dev": True,
                "img": "database",
                "gen": database.page
            },
            "exam_add": {
                "dev": True,
                "img": "add",
                "gen": add.page
            }
        }
    }
    with context.Context(req) as ctx:
        return base.gen_composite_page(
            ctx,
            layout,
            sub_page,
            sub_page_args={"exm_id": exm_id}
        )
