from webamc.www.all import *


router = fa.APIRouter()


@router.get("/profile/page/main")
def route_profile_page(
        req: fa.Request,
        sub_page: None | str = None
) -> fa.Response:
    from .page import personal_data, groups
    layout: base.page_layout_t = {
        "title": "page_title_profile",
        "path": "/profile/page/main",
        "default": "personal_data",
        "sub_pages": {
            "personal_data": (True, "person", personal_data.page),
            "group": (True, "group", groups.page)
        }
    }
    with context.Context(req) as ctx:
        session.check_logged_in(ctx)
        result = base.gen_composite_page(ctx, layout, sub_page, wip=True)
    return result
