#!/usr/bin/env python3

from webamc.www.all import *
from webamc import project


def data(
        ctx: context.Context,
        file_id: project.file_id_t,
        file_content: fa.UploadFile,
        project_code: str
) -> fa.Response:
    upload_result: types.oper_code_t = "err"
    if file_id == "project_archive":
        suffix = ".zip"
    elif file_id == "answer_sheets":
        suffix = ".pdf"
    elif file_id == "student_list":
        suffix = ".csv"
    else:
        assert False
        
    content = file_content.file.read()
    with tempfile.NamedTemporaryFile(
            mode="wb", suffix=suffix, delete=False
    ) as tmp_file:
        tmp_file.write(content)
        tmp_file.close()
        upload_result = project.action_upload(
            session.usr_code(ctx),
            project_code,
            file_id,
            tmp_file.name
        )
    os.remove(tmp_file.name)
    return base.wrap_code(upload_result)
