from webamc.www.all import *


def data(ctx: context.Context) -> fa.Response:
    session.check_active_registration(ctx)
    session.clear_active_registration(ctx)
    return base.wrap_code("succ")
