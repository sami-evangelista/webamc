from cas import CASClient  # type: ignore

from webamc.www.all import *
from webamc.db import queries


cas_client_init = False
cas_client: CASClient


def data(
        ctx: context.Context,
        ticket: str | None,
        next_url: str | None
) -> fa.Response:
    if not config.CONFIG["auth_cas_enabled"]:
        raise fa.HTTPException(status_code=403)
    if ticket is None:
        return base.redirect(get_cas_client().get_login_url())

    # verify the ticket.  this may raise an exception
    try:
        user, _, _ = get_cas_client().verify_ticket(ticket)
    except:
        user = None

    # cas login unsuccessful or logged user cannot use the
    # application
    if user is None or not _cas_login_check(ctx, user):
        raise fa.HTTPException(status_code=403)

    # redirect to next url if it has been provided
    if next_url is not None:
        return base.redirect(next_url)
    return base.redirect(base.mkuri("/"))


def _cas_login_check(ctx: context.Context, login: str) -> bool:
    usr = queries.get_usr_by_cas_auth(ctx.dbs, login)
    if usr is None:
        return False
    session.init(ctx, usr)
    return True


def _cas_init_client() -> None:
    global cas_client, cas_client_init
    if not cas_client_init:
        url = config.CONFIG["base_url"]
        url += base.mkuri("/auth/oper/login-cas")
        cas_client = CASClient(
            version=config.CONFIG["cas_version"],
            service_url=url,
            server_url=config.CONFIG["cas_server"]
        )
        cas_client_init = True


def get_cas_client() -> CASClient:
    _cas_init_client()
    return cas_client
