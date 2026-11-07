from webamc.www.all import *


router = fa.APIRouter()


@router.get("/mcq/page/form")
def page_form(
        req: fa.Request,
        mode: types.mcq_form_mode_t,
        itm_id: None | int = None,
        sub_id: None | int = None
) -> fa.Response:
    from .page import form
    with context.Context(req) as ctx:
        return form.page(ctx, mode, itm_id, sub_id)


@router.post("/mcq/oper/save")
def oper_save(req: fa.Request, args: types.args_oper_t) -> fa.Response:
    from .oper import save
    with context.Context(req) as ctx:
        return save.data(ctx, args)


@router.post("/mcq/oper/finish")
def oper_finish(req: fa.Request) -> fa.Response:
    from .oper import finish
    with context.Context(req) as ctx:
        return finish.data(ctx)
