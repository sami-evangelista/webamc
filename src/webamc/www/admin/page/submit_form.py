from webamc.www.all import *


def page(
        ctx: context.Context,
        **kwargs: tp.Unpack[types.args_route_admin_tbl_t]
) -> he.Element:
    input_csv = he.Input(
        type_="file",
        id_="csv_file",
        name="csv_file"
    )
    uri = base.mkuri("/admin/oper/submit")
    js = f"base_submit_file('csv_file', '{uri}', 'div-submit-result')"
    a_submit = base.static_img(
        "checkmark",
        "word_send",
        js=js,
        class_="submit"
    )
    p_csv_file = he.P(
        he.Txt("seq_csv_file"), input_csv
    )
    div_file = he.Div(p_csv_file, a_submit, class_="box")
    div_result = he.Div(id_="div-submit-result")
    return he.ElementList(div_file, div_result)
