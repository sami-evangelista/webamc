from webamc import project
from webamc.www.all import *
from webamc.www.project import util


def data(
        ctx: context.Context,
        prj_id: int,
        action: types.action_t,
        ufile: fa.UploadFile
) -> fa.Response:
    content = ufile.file.read()
    code = project.action(
        ctx.dbs,
        session.usr_id(ctx),
        util.get_project(ctx, prj_id),
        action,
        fname=ufile.filename,
        fcontent=content
    )
    return base.wrap_code(code)
