#!/usr/bin/env python3

from webamc.www.all import *
from webamc import project


def data(ctx: context.Context, args: dict[str, tp.Any]) -> fa.Response:
    proj = project.Project(session.usr_code(ctx), args["code"])
    code, ids = proj.update_data_untyped(args)
    return base.wrap_code(code, ids)
