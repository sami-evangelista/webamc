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
    from .page import main
    with context.Context(req) as ctx:
        return main.page(ctx)


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
