from webamc.www.all import *
from webamc.www.project import util
from webamc.util import fmt
from webamc import project


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:
    prj = util.get_project(ctx, args["prj_id"])
    files = dict()
    for f, fdata in project.list_files(prj).items():
        files[f] = {
            "name": project.file_name(f),
            "exists": fdata["exists"]
        }
        if fdata["date"] is not None:
            files[f]["date"] = fmt.fmt_datetime(fdata["date"])
        if fdata["exists"]:
            files[f]["uri"] = base.mkuri(
                "/project/page/get-file",
                prj_id=prj.prj_id,
                file_name=project.file_name(f)
            )
    response_data = {
        "files": files,
        "doable": project.doable(ctx.dbs, prj),
        "done": json.loads(prj.prj_done),
        "warning": project.warning(prj)
    }
    return base.wrap_code("succ", data=response_data)
