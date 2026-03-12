#!/usr/bin/env python3

from webamc.www.all import *
from webamc.www.project import router
from webamc.util import fmt
from webamc import project


def page(
        ctx: context.Context,
        project_code: str,
        file_name: str
) -> fa.Response:
    file_data = project.get_file(
        session.usr_code(ctx),
        project_code,
        file_name
    )
    if file_data is None:
        return base.page_error(ctx, 404)
    path, file_name = file_data
    return fa.responses.FileResponse(
        path,
        media_type=mtype.get_media_type(path),
        filename=file_name
    )
