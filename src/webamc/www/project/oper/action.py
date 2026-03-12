#!/usr/bin/env python3

from webamc.www.all import *
from webamc.www.project import router
from webamc import project


def data(
        ctx: context.Context,
        args: router.args_oper_action_t
) -> fa.Response:
    msgs, data = project.action(
        session.usr_code(ctx),
        args["project_code"],
        args["action"],
        args["action_params"]
    )
    response: types.json_response_t = {
        "success": not any(x.startswith("err") for x in msgs),
        "msgs": [lang.txt(m) for m in msgs],
        "result": data
    }
    return fa.responses.JSONResponse(response)
