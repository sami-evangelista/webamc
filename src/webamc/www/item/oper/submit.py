#!/usr/bin/env python3

from webamc.www.all import *


def data(
        ctx: context.Context,
        zip_file: fa.UploadFile
) -> types.json_response_t:
    def error_result(err: str) -> types.json_response_t:
        return {
            "success": False,
            "msgs": [lang.txt(err)],
            "result": None
        }
    result: types.json_response_t
    content = zip_file.file.read()
    if len(content) == 0:
        return error_result("err_item_admin_empty_archive")
    with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".zip", delete=False
    ) as tmp_file:
        tmp_file.write(content)
        tmp_file.close()
        load_result = base.generic_load_file(
            tmp_file.name, "archive", usr_id=session.usr_id(ctx)
        )
        result = {
            "success": True,
            "msgs": list(),
            "result": load_result
        }
    os.remove(tmp_file.name)
    return result
