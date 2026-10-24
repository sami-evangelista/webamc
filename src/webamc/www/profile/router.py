from webamc.www.all import *


router = fa.APIRouter()


@router.get("/profile/page/main")
def page_main(req: fa.Request) -> fa.Response:
    from .page import main
    with context.Context(req) as ctx:
        session.check_logged_in(ctx)
        return main.page(ctx)
