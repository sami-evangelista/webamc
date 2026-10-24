from webamc.www.all import *


router = fa.APIRouter()


@router.get("/ticket/page/main")
def page_main(req: fa.Request, ticket: str) -> fa.Response:
    from .page import main
    with context.Context(req) as ctx:
        return main.page(ctx, ticket)


@router.post("/ticket/oper/send")
def oper_send(req: fa.Request, args: types.args_oper_t) -> fa.Response:
    from .oper import send
    with context.Context(req) as ctx:
        return send.data(ctx, args)


@router.post("/ticket/oper/password-change")
def oper_password_change(
        req: fa.Request,
        args: types.args_oper_t
) -> fa.Response:
    from .oper import password_change
    with context.Context(req) as ctx:
        return password_change.data(ctx, args)


@router.post("/ticket/oper/account-creation")
def oper_account_creation(
        req: fa.Request,
        args: types.args_oper_t
) -> fa.Response:
    from .oper import account_creation
    with context.Context(req) as ctx:
        return account_creation.data(ctx, args)
