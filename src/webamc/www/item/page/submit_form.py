from webamc.www.all import *
from webamc.www.item import router


def page(
        ctx: context.Context,
        **kwargs: tp.Unpack[router.args_page_item_t]
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
        "verb_send",
        js=js,
        class_="submit"
    )
    p_zip_file = he.P(
        base.mkhelp(
            he.Span(he.Txt("seq_zip_file")),
            "seq_zip_file",
            "item_submit"
        ),
        input_zip
    )
    div_file = he.Div(p_zip_file, a_submit, class_="box")
    div_result = he.Div(id_="div-submit-result")
    result = he.ElementList(div_file, div_result)
    return result
