from webamc.www.all import *


router = fa.APIRouter()
args_oper_login_local_t = tp_ext.TypedDict(
    "args_oper_login_local_t", {
        "loc_login": str,
        "loc_password": str
    }
)


@router.get("/auth/page/main")
def route_auth_page(
        req: fa.Request,
        sub_page: str = ""
) -> fa.Response:
    from .page import password_change, login_local, creation, login_cas
    sub_pages: dict[str, base.sub_page_spec_t] = dict()
    default = "login-local"
    if config.CONFIG["auth_cas_enabled"]:
        sub_pages["login-cas"] = (False, "server", login_cas.page)
        default = "login-cas"
    if config.CONFIG["auth_local_enabled"]:
        sub_pages["login-local"] = (False, "password", login_local.page)
        sub_pages["password-change"] = (False, "mail", password_change.page)
    if config.CONFIG["auth_account_creation_enabled"]:
        sub_pages["creation"] = (False, "person-add", creation.page)
    layout: base.page_layout_t = {
        "title": "page_title_authentication",
        "path": "/auth/page/main",
        "default": default,
        "sub_pages": sub_pages
    }
    with context.Context(req) as ctx:
        return base.gen_composite_page(ctx, layout, sub_page)


@router.get("/auth/oper/login-cas")
def route_auth_oper_login_cas(
        req: fa.Request,
        ticket: str | None = None,
        next_url: str | None = None
) -> fa.Response:
    from .oper import login_cas
    with context.Context(req) as ctx:
        return login_cas.data(ctx, ticket, next_url)


@router.get("/auth/oper/logout")
def route_auth_oper_logout(req: fa.Request) -> fa.Response:
    from .oper import logout
    with context.Context(req) as ctx:
        return logout.data(ctx)


@router.post("/auth/oper/login-local")
def route_auth_oper(
        req: fa.Request,
        args: args_oper_login_local_t
) -> fa.Response:
    from .oper import login_local
    with context.Context(req) as ctx:
        return login_local.data(ctx, args)
