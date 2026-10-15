from webamc.www.all import *
from webamc.www.item import router


def page(
        ctx: context.Context,
        **kwargs: tp.Unpack[router.args_item_t]
) -> he.Element:
    input_zip = he.Input(
        id_="zip_file",
        type_="file",
        name="zip_file"
    )
    uri = base.mkuri("/item/oper/submit")
    js = f"base_submit_file('zip_file', '{uri}', 'div-submit-result')"
    a_submit = base.static_img(
        "checkmark",
        "word_send",
        js=js,
        class_="submit"
    )
    trs: list[list[he.Element]] = [
        [he.Txt("seq_zip_file"), input_zip]
    ]
    table = he.mktable(trs, class_="table-form")
    div_file = he.Div(table, a_submit, class_="box")
    div_result = he.Div(id_="div-submit-result")
    result = he.ElementList(div_file, div_result)
    return result
