from webamc.www.all import *


def data(
        ctx: context.Context,
        zip_file: fa.UploadFile
) -> fa.responses.Response:
    content = zip_file.file.read()
    if len(content) == 0:
        return base.wrap_code("err_item_admin_empty_archive")
    with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".zip", delete=False
    ) as tmp_file:
        tmp_file.write(content)
        tmp_file.close()
        load_result = base.generic_load_file(
            tmp_file.name, "archive", usr_id=session.usr_id(ctx)
        )
    os.remove(tmp_file.name)
    return base.wrap_code("succ", load_result)
