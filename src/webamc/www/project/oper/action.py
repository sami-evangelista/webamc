from webamc.www.all import *
from webamc.www.project import router
from webamc import project


def data(
        ctx: context.Context,
        args: router.args_oper_action_t
) -> fa.Response:
    if args["action"] == "new":
        code = project.Project.new(
            session.usr_code(ctx),
            session.usr_name(ctx),
            args["project_code"]
        )
    else:
        code = project.Project(
            session.usr_code(ctx),
            session.usr_name(ctx),
            args["project_code"],
            dbs=ctx.dbs
        ).action(
            args["action"],
            args["action_params"]
        )
    response: types.json_response_t = {
        "success": not code.startswith("err"),
        "msgs": [lang.txt(types.oper_code_to_txt(code))],
        "result": None
    }
    return fa.responses.JSONResponse(response)
