from webamc.www.all import *
from webamc import project


def page(
        ctx: context.Context,
        project_code: str,
        file_name: str
) -> fa.Response:
    file_data = project.Project(
        session.usr_code(ctx),
        session.usr_name(ctx),
        project_code
    ).get_file(
        file_name
    )
    if file_data is None:
        return base.page_error(ctx, 404)
    path, name = file_data
    return fa.responses.FileResponse(
        path,
        media_type=mtype.get_media_type(path),
        filename=name
    )
