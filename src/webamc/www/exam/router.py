from webamc.www.all import *
from webamc.db import queries, tables


router = fa.APIRouter()

args_page_dashboard_exam_t = tp_ext.TypedDict(
    "args_page_dashboard_exam_t", {
        "exm_id": int
    }
)
args_page_exam_t = tp_ext.TypedDict("args_page_exam_t", {
    "exm_id": int
})
args_oper_register_group_t = tp_ext.TypedDict("args_oper_register_group_t", {
    "exm_id": int,
    "grp_id": int
})


def _get_exam(
        ctx: context.Context,
        exm_id: int
) -> tuple[tables.Mcq, tables.Item, tables.Exam]:
    result = next(
        (mcq_item_exam
         for mcq_item_exam in queries.get_usr_exams(
                 ctx.dbs, session.usr_id(ctx)
         )
         if mcq_item_exam[2].exm_id == exm_id), None
    )
    if result is None:
        raise fa.HTTPException(status_code=403)
    return result


@router.post("/exam/oper/register-group")
def route_oper_register_group(
        req: fa.Request,
        args: args_oper_register_group_t
) -> fa.Response:
    from .oper import register_group
    with context.Context(req) as ctx:
        return register_group.data(ctx, args)


@router.post("/exam/page/dashboard-exam")
def route_page_dashboard_exam(
        req: fa.Request,
        args: args_page_dashboard_exam_t
) -> fa.Response:
    from .page import dashboard_exam
    with context.Context(req) as ctx:
        return dashboard_exam.page(ctx, args)


@router.get("/exam/page/main")
def route_exam_page(
        req: fa.Request,
        sub_page: None | str = None,
        exm_id: None | int = None
) -> fa.Response:
    from .page import creation, database, dashboard
    layout: base.page_layout_t = {
        "title": "page_title_exam",
        "path": "/exam/page/main",
        "default": "database",
        "sub_pages": {
            "database": (True, "database", database.page),
            "creation": (True, "add", creation.page),
            "dashboard": (True, "list", dashboard.page)
        }
    }
    with context.Context(req) as ctx:
        return base.gen_composite_page(
            ctx,
            layout,
            sub_page,
            sub_page_args={"exm_id": exm_id}
        )
