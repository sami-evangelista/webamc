from webamc.www.all import *
from webamc import project


def data(
        ctx: context.Context,
        action: project.action_t,
        ufile: fa.UploadFile,
        project_code: str
) -> fa.Response:
    upload_result: types.oper_code_t = "err"
    content = ufile.file.read()
    upload_result = project.Project(
        session.usr_code(ctx),
        session.usr_name(ctx),
        project_code
    ).action(
        action,
        dict(),
        fname=ufile.filename,
        fcontent=content
    )
    return base.wrap_code(upload_result)
