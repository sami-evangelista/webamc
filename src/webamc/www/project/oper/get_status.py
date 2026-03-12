#!/usr/bin/env python3

from webamc.www.all import *
from webamc.www.project import router
from webamc import project


def data(
        ctx: context.Context,
        args: router.args_project_code_t
) -> fa.Response:
    status, files = project.get_status_and_files(
        session.usr_code(ctx),
        args["project_code"]
    )
    response_result = {
        "status": status,
        "files": files
    }
    return base.wrap_code("succ", response_result)
