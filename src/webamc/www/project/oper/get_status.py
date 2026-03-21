#!/usr/bin/env python3

from webamc.www.all import *
from webamc.www.project import router
from webamc.util import fmt
from webamc import project


def data(
        ctx: context.Context,
        args: router.args_project_code_t
) -> fa.Response:
    proj = project.Project(session.usr_code(ctx), args["project_code"])
    status = proj.status()
    files = dict()
    for f, fdata in status["files"].items():
        files[f] = {
            "name": project.file_name(f),
            "exists": fdata["exists"]
        }
        if fdata["date"] is not None:
            files[f]["date"] = fmt.fmt_datetime(fdata["date"])
        if fdata["exists"]:
            files[f]["uri"] = base.mkuri(
                "/project/page/get-file",
                project_code=proj.pcode,
                file_name=project.file_name(f)
            )
    response = {
        "data": status["data"],
        "done": status["done"],
        "doable": status["doable"],
        "history": status["history"],
        "files": files
    }
    return base.wrap_code("succ", response)
