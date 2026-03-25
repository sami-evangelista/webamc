from webamc.www.all import *
from webamc import project


def page(
        ctx: context.Context,
        usr_code: str,
        usr_name: str,
        project_code: str
) -> fa.Response:
    file_data = project.Project(
        usr_code,
        usr_name,
        project_code
    ).mail_pdf(
        session.usr_code(ctx)
    )
    if file_data is None:
        return base.page_error(ctx, 404)
    path, file_name = file_data
    return fa.responses.FileResponse(
        path,
        media_type=mtype.get_media_type(".pdf"),
        filename=file_name
    )
