from webamc.www.all import *


router = fa.APIRouter()


@router.get("/auth/page/main")
def page_main(
        req: fa.Request,
        sub_page: str = ""
) -> fa.Response:
    from .page import main
    with context.Context(req) as ctx:
        return main.page(ctx)


@router.get("/auth/oper/login-cas")
def oper_login_cas(
        req: fa.Request,
        args: types.args_oper_t
) -> fa.Response:
    from .oper import login_cas
    with context.Context(req) as ctx:
        return login_cas.data(ctx, args)


@router.get("/auth/oper/logout")
def oper_logout(req: fa.Request) -> fa.Response:
    from .oper import logout
    with context.Context(req) as ctx:
        return logout.data(ctx)


@router.post("/auth/oper/login-local")
def oper_login_local(
        req: fa.Request,
        args: types.args_oper_t
) -> fa.Response:
    from .oper import login_local
    with context.Context(req) as ctx:
        return login_local.data(ctx, args)
