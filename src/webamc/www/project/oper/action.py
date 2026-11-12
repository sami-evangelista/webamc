from webamc import project
from webamc.db import tables
from webamc.www.all import *
from webamc.www.project import util


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:

    response_result: tp.Any = None

    if args["action"] == "new":

        # action new is handled diffrently
        done: types.project_actions_done_t = {
            a: False
            for a in types.literal_type_values(types.action_t)
        }
        done["new"] = True
        prj = tables.Project(
            prj_code=args["prj_code"],
            prj_usr=session.usr_id(ctx),
            prj_done=json.dumps(done),
            prj_history=json.dumps(list())
        )
        ctx.dbs.add(prj)
        ctx.dbs.flush()
        code: types.oper_code_t = "succ"
        response_result = {
            "prj_id": prj.prj_id
        }

    else:

        # any other (non upload) action
        code = project.action(
            ctx.dbs,
            session.usr_id(ctx),
            util.get_project(ctx, args["prj_id"]),
            args["action"],
            args["action_params"]
        )
        response_result = None

    return base.wrap_code(code, result=response_result)
