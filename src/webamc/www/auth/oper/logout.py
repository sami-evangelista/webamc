from webamc.www.all import *


def data(
        ctx: context.Context
) -> fa.Response:
    session.logout(ctx)
    return base.redirect_to_login_url()
