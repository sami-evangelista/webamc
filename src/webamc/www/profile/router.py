from webamc.www.all import *


router = fa.APIRouter()


@router.get("/profile/page/main")
def route_profile_page(
        req: fa.Request,
        sub_page: None | str = None
) -> fa.Response:
    from .page import main
    with context.Context(req) as ctx:
        session.check_logged_in(ctx)
        return main.page(ctx)
