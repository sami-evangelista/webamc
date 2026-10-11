from webamc.www.all import *
from webamc.actions import loadcsv


def data(
        ctx: context.Context,
        csv_file: fa.UploadFile
) -> fa.responses.Response:
    def error_result(err: types.txt_t) -> fa.responses.Response:
        return base.wrap_errors(lang.txt(err))
    result: fa.responses.Response
    content = csv_file.file.read()
    if len(content) == 0:
        return error_result("err_admin_empty_csv_file")
    with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".csv", delete=False
    ) as tmp_file:
        tmp_file.write(content)
        tmp_file.close()
        tbl_name = loadcsv.get_tbl_name(tmp_file.name, ";")
        if tbl_name is None:
            result = error_result("err_admin_table_undeterminable")
        elif not session.can_admin_table(ctx, tbl_name):
            result = error_result("err_admin_no_right_to_update_table")
        else:
            load_result = base.generic_load_file(
                tmp_file.name, "csv", csv_delimiter=";"
            )
            result = fa.responses.JSONResponse({
                "success": True,
                "msgs": list(),
                "result": load_result
            })
    os.remove(tmp_file.name)
    return result
