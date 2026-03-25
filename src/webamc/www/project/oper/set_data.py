from webamc.www.all import *
from webamc import project


def data(ctx: context.Context, args: dict[str, tp.Any]) -> fa.Response:
    code, ids = project.Project(
        session.usr_code(ctx),
        session.usr_name(ctx),
        args["code"],
        dbs=ctx.dbs
    ).set_data(
        args
    )
    return base.wrap_code(code, ids)
