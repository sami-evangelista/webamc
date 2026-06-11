from webamc.www.all import *


def data(ctx: context.Context) -> fa.Response:
    session.check_active_registration(ctx)
    session.clear_active_registration(ctx)
    response = {
        "success": True,
        "msgs": list(),
        "result": None
    }
    return fa.responses.JSONResponse(response)
