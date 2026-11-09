from webamc.www.all import *
from webamc.www.exam import util
from webamc.db import queries, tables


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:
    exm_id = args["exm_id"]
    exam = util.get_exam(ctx, exm_id)[1]
    raise ValueError
    response = {
        "success": True,
        "msgs": list(),
        "result": None
    }
    return fa.responses.JSONResponse(response)
