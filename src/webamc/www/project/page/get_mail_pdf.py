#!/usr/bin/env python3

from webamc.www.all import *
from webamc.www.project import router
from webamc.util import fmt
from webamc import project


def page(
        ctx: context.Context,
        usr_code: str,
        project_code: str
) -> fa.Response:
    file_data = project.get_mail_pdf(
        session.usr_eaddr(ctx),
        usr_code,
        project_code
    )
    if file_data is None:
        return base.page_error(ctx, 404)
    path, file_name = file_data
    return fa.responses.FileResponse(
        path,
        media_type=mtype.get_media_type(".pdf"),
        filename=file_name
    )
