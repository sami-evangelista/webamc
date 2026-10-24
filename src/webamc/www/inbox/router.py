from webamc.www.all import *


router = fa.APIRouter()


@router.get("/inbox/page/msg")
def page_msg(req: fa.Request, msg_id: int) -> fa.Response:
    from .page import msg
    with context.Context(req) as ctx:
        return msg.page(ctx, msg_id)


@router.get("/inbox/page/main")
def page_main(req: fa.Request) -> fa.Response:
    from .page import main
    with context.Context(req) as ctx:
        return main.page(ctx)
