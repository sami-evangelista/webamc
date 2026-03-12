#!/usr/bin/env python3

from webamc.www.all import *
from webamc import project


def data(ctx: context.Context, args: dict[str, str]) -> fa.Response:
    code, ids = project.update_data(session.usr_code(ctx), args)
    return base.wrap_code(code, ids)
