#!/usr/bin/env python3

from webamc.www.all import *
from webamc.www.project import router
from webamc import project


def data(
        ctx: context.Context,
        args: router.args_oper_action_t
) -> fa.Response:
    if args["action"] == "new":
        code = project.Project.new(session.usr_code(ctx), args["project_code"])
        data = None
    else:
        proj = project.Project(session.usr_code(ctx), args["project_code"])
        code = project.Project(
            session.usr_code(ctx), args["project_code"]
        ).action(
            args["action"],
            args["action_params"],
            ctx.dbs
        )
    response: types.json_response_t = {
        "success": not code.startswith("err"),
        "msgs": [lang.txt(code)],
        "result": None
    }
    return fa.responses.JSONResponse(response)
