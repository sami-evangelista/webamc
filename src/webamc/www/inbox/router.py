from webamc.www.all import *


router = fa.APIRouter()


@router.get("/inbox/page/msg")
def route_inbox_page_msg(req: fa.Request, msg_id: int) -> fa.Response:
    from .page import msg
    with context.Context(req) as ctx:
        return msg.page(ctx, msg_id)


@router.get("/inbox/page/list")
def route_inbox_page_list(req: fa.Request) -> fa.Response:
    from .page import list as lst
    with context.Context(req) as ctx:
        return lst.page(ctx)
