from webamc import project
from webamc.www.all import *
from webamc.www.project import util


def page(
        ctx: context.Context,
        prj_id: int,
        file_name: str
) -> fa.Response:
    file_data = project.get_file(util.get_project(ctx, prj_id), file_name)
    if file_data is None:
        return base.page_error(404)
    path, name = file_data
    return fa.responses.FileResponse(
        path,
        media_type=mtype.get_mtype(path),
        filename=name
    )
