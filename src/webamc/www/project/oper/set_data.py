from webamc.www.all import *
from webamc import project


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:
    project_data = args["project_data"]
    code, ids = project.Project(
        session.usr_code(ctx),
        session.usr_name(ctx),
        project_data["code"],
        dbs=ctx.dbs
    ).set_data(
        project_data
    )
    return base.wrap_code(code, ids)
