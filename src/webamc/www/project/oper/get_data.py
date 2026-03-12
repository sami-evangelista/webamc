#!/usr/bin/env python3

from webamc.www.all import *
from webamc.www.project import router
from webamc import project


def data(
        ctx: context.Context,
        args: router.args_project_code_t
) -> fa.Response:
    data = project.get_data(
        session.usr_code(ctx),
        args["project_code"]
    )
    return base.wrap_code("succ", data)
