#!/usr/bin/env python3

from webamc.www.all import *


router = fa.APIRouter()

args_mcq_result_t = tp_ext.TypedDict("args_mcq_result_t", {
    "mcq_id": int,
    "mcq_choices": dict[int, bool],
    "mcq_questions": dict[int, dict[int, bool]]
})


@router.get("/mcq/page/form")
def route_mcq_page_form(
        req: fa.Request,
        mcq_id: int,
        iti_num: int | None = None # to get specific instance
) -> fa.Response:
    from .page import form
    with context.Context(req) as ctx:
        return form.page(ctx, mcq_id, iti_num)


@router.post("/mcq/oper/correction")
def route_mcq_oper_correction(
        req: fa.Request,
        mcq_result: args_mcq_result_t
) -> fa.Response:
    from .oper import correction
    with context.Context(req) as ctx:
        return correction.data(ctx, mcq_result)


@router.post("/mcq/oper/save")
def route_mcq_oper_save(
        req: fa.Request,
        mcq_result: args_mcq_result_t
) -> fa.Response:
    from .oper import save
    with context.Context(req) as ctx:
        return save.data(ctx, mcq_result)


@router.post("/mcq/oper/finish")
def route_mcq_oper_finish(
        req: fa.Request
) -> fa.Response:
    from .oper import finish
    with context.Context(req) as ctx:
        return finish.data(ctx)
