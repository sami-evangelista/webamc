#!/usr/bin/env python3

from webamc.www.all import *
from webamc import project


def data(
        ctx: context.Context,
        action: project.action_t,
        file_content: fa.UploadFile,
        project_code: str
) -> fa.Response:
    upload_result: types.oper_code_t = "err"
    content = file_content.file.read()
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tmp_file:
        tmp_file.write(content)
        tmp_file.close()
        upload_result = project.Project(
            session.usr_code(ctx),
            project_code,
        ).action_upload(
            action,
            tmp_file.name
        )
    os.remove(tmp_file.name)
    return base.wrap_code(upload_result)
