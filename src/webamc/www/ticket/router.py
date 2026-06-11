from webamc.www.all import *


router = fa.APIRouter()

args_oper_account_creation_t = tp_ext.TypedDict(
    "args_oper_account_creation_t",
    {
        "ticket": str,
        "usr_code": str,
        "usr_eaddr": str,
        "usr_fst_name": str,
        "usr_name": str,
        "loc_password": str,
        "loc_password_confirm": str
    }
)
args_oper_send_t = tp_ext.TypedDict(
    "args_oper_send_t",
    {
        "usr_eaddr": str,
        "tkt_type": types.ticket_type_t
    }
)
args_oper_password_change_t = tp_ext.TypedDict(
    "args_oper_password_change_t",
    {
        "ticket": str,
        "loc_password": str,
        "loc_password_confirm": str
    }
)


@router.get("/ticket/page/main")
def route_page_main(
        req: fa.Request,
        ticket: str
) -> fa.Response:
    from .page import ticket as ticket_page
    with context.Context(req) as ctx:
        return ticket_page.page(ctx, ticket)


@router.post("/ticket/oper/send")
def route_oper_send(
        req: fa.Request,
        args: args_oper_send_t
) -> fa.Response:
    from .oper import send
    with context.Context(req) as ctx:
        return send.data(ctx, args)


@router.post("/ticket/oper/password-change")
def route_oper_password_change(
        req: fa.Request,
        args: args_oper_password_change_t
) -> fa.Response:
    from .oper import password_change
    with context.Context(req) as ctx:
        return password_change.data(ctx, args)


@router.post("/ticket/oper/account-creation")
def route_oper_account_creation(
        req: fa.Request,
        args: args_oper_account_creation_t
) -> fa.Response:
    from .oper import account_creation
    with context.Context(req) as ctx:
        return account_creation.data(ctx, args)
